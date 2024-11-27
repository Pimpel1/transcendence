import logging

from django.db import transaction

from .. import lock
from ..models import Tournament, Game, Round, Player, LeaderboardEntry
from . import channels as channels_utils
from . import game as game_utils
from . import player as player_utils


logger = logging.getLogger('matchmaker-service')


def create(
    pool_size,
    tournament_name="Unnamed Tournament",
    type=Tournament.ONLINE
):
    lock.acquire('tournament')

    try:
        if (pool_size < 2):
            raise ValueError('Pool size must be at least 2')
        with transaction.atomic():
            tournament = Tournament.objects.create(
                    pool_size=pool_size,
                    name=tournament_name,
                    type=type,
                )
            logger.info(
                f'Created {type} tournament for '
                f'{pool_size} players '
                f'\'{tournament_name}\' (ID: {tournament.id})'
            )
        return tournament

    except Exception as e:
        raise Exception(
            f'Error creating {type} tournament for {pool_size} players '
            f'\'{tournament_name}\' [{e}]'
        )

    finally:
        lock.release('tournament')


def registration(
    pool_size,
    tournament_name="Unnamed Tournament",
    players=None,
    type=Tournament.ONLINE
):
    if players is None:
        players = []
    elif isinstance(players, str):
        players = [players]
    players = list(set(players))

    try:
        tournament = create(pool_size, tournament_name, type)
        for player_name in players:
            join(tournament.id, player_name, type)
        return tournament.id

    except Exception as e:
        logger.error(f'Error registering tournament {tournament_name} [{e}]')


def leave(tournament_id, player_name, type=Tournament.ONLINE):
    logger.info(f'{player_name} leaves tournament (ID: {tournament_id})')

    if player_name is None or player_name == '':
        raise Exception('Player name is required')

    if type != Tournament.ONLINE:
        leave_local_tournament(tournament_id, player_name)
    else:
        leave_online_tournament(tournament_id, player_name)


def leave_local_tournament(tournament_id, player_name):
    lock.acquire('tournament')

    try:
        with transaction.atomic():
            tournament = Tournament.objects.get(
                id=tournament_id
            )
            if tournament.status != Tournament.WAITING_FOR_PLAYERS:
                raise Exception(
                    f'Tournament \'{tournament.name}\' '
                    f' (ID: {tournament_id}) is already underway or finished'
                )
            if player_name not in tournament.player_names:
                raise Exception(
                    f'Player "{player_name}" is not registered for '
                    f'tournament \'{tournament.name}\' '
                    f'(ID: {tournament_id})'
                )
            tournament.player_names.remove(player_name)
            tournament.save()

    except Exception as e:
        raise Exception(
            f'Error removing player {player_name} '
            f'from local tournament (ID: {tournament_id}) [{e}]'
        )

    finally:
        lock.release('tournament')


def leave_online_tournament(tournament_id, player_name):
    player, _ = player_utils.get_or_create(player_name)

    lock.acquire('tournament')

    try:
        with transaction.atomic():
            tournament = Tournament.objects.get(
                id=tournament_id
            )
            if tournament.status != Tournament.WAITING_FOR_PLAYERS:
                raise Exception(
                    f'Tournament \'{tournament.name}\' '
                    f' (ID: {tournament_id}) is already underway or finished'
                )
            if player not in tournament.players.all():
                raise Exception(
                    f'Player "{player_name}" is not registered for '
                    f'tournament \'{tournament.name}\' '
                    f'(ID: {tournament_id})'
                )
            tournament.players.remove(player)
            tournament.player_names.remove(player_name)
            tournament.save()

    except Exception as e:
        raise Exception(
            f'Error removing player {player_name} '
            f'from online tournament (ID: {tournament_id}) [{e}]'
        )

    finally:
        lock.release('tournament')


def add_player(tournament_id, player_name, type=Tournament.ONLINE):
    logger.info(f'{player_name} joins tournament (ID: {tournament_id})')

    if player_name is None or player_name == '':
        raise Exception('Player name is required')

    if type != Tournament.ONLINE:
        add_local_player(tournament_id, player_name)
    else:
        add_online_player(tournament_id, player_name)


def add_local_player(tournament_id, player_name):
    lock.acquire('tournament')

    try:
        with transaction.atomic():
            tournament = Tournament.objects.get(
                id=tournament_id
            )
            if tournament.status != Tournament.WAITING_FOR_PLAYERS:
                raise Exception(
                    f'Tournament \'{tournament.name}\' '
                    f' (ID: {tournament_id}) is not accepting players'
                )
            if player_name in tournament.player_names:
                raise Exception(
                    f'Player "{player_name}" is already in '
                    f'tournament \'{tournament.name}\' '
                    f'(ID: {tournament_id})'
                )
            tournament.player_names.append(player_name)
            tournament.save()

    except Exception as e:
        raise Exception(
            f'Failed to add player {player_name} '
            f'to local tournament (ID: {tournament_id}) [{e}]'
        )

    finally:
        lock.release('tournament')


def add_online_player(tournament_id, player_name):
    player, _ = player_utils.get_or_create(player_name)

    lock.acquire('tournament')

    try:
        with transaction.atomic():
            tournament = Tournament.objects.get(
                id=tournament_id
            )
            if tournament.status != Tournament.WAITING_FOR_PLAYERS:
                raise Exception(
                    f'Tournament \'{tournament.name}\' '
                    f' (ID: {tournament_id}) is not accepting players'
                )
            if player in tournament.players.all():
                raise Exception(
                    f'Player "{player_name}" is already in '
                    f'tournament "{tournament.name}" (ID: {tournament_id})'
                )
            tournament.players.add(player)
            tournament.player_names.append(player_name)
            tournament.save()

    except Exception as e:
        raise Exception(
            f'Failed to add player {player_name} '
            f'to online tournament (ID: {tournament_id}) [{e}]'
        )

    finally:
        lock.release('tournament')


def join(tournament_id, player_name, type=Tournament.ONLINE):
    try:
        add_player(tournament_id, player_name, type)
        started = start(tournament_id)
        if started:
            logger.info(f'Tournament (ID: {tournament_id}) has started')
            channels_utils.send_tournament_start(
                Tournament.objects.get(id=tournament_id)
            )
            start_next_round(tournament_id)

    except Exception as e:
        logger.error(
            f'Error joining tournament (ID: {tournament_id}) '
            f'as {player_name} [{e}]'
        )
        raise


def start(tournament_id):
    lock.acquire('tournament')

    try:
        with transaction.atomic():
            tournament = Tournament.objects.get(
                id=tournament_id
            )
            if tournament.status != Tournament.WAITING_FOR_PLAYERS \
                    or len(tournament.player_names) < tournament.pool_size:
                return False

            tournament.status = Tournament.IN_PROGRESS
            if tournament.type != Tournament.ONLINE:
                generate_local_games(tournament)
            else:
                generate_online_games(tournament)

            for player_name in tournament.player_names:
                LeaderboardEntry.objects.create(
                    tournament=tournament,
                    player_name=player_name
                )

            tournament.save()
            return True

    except Exception as e:
        logger.error(f'Error starting tournament (ID: {tournament_id}) [{e}]')
        return False

    finally:
        lock.release('tournament')


def generate_local_games(tournament):
    players = list(tournament.player_names)
    if len(players) % 2 == 1:
        players.append(None)

    for round_number in range(1, len(players)):
        create_local_round(tournament, players, round_number)
        players.insert(1, players.pop())


def create_local_round(tournament, players, round_number):
    round = Round.objects.create(
        tournament=tournament,
        round_number=round_number,
        type=Round.LOCAL
    )

    for i in range(len(players) // 2):
        player1 = players[i]
        player2 = players[len(players) - 1 - i]
        if player1 is not None and player2 is not None:
            game_utils.create(
                player1=player1,
                player2=player2,
                type=Game.LOCAL,
                status=Game.SCHEDULED,
                tournament=tournament,
                round=round,
            )


def generate_online_games(tournament):
    players = list(tournament.players.all())
    if len(players) % 2 == 1:
        players.append(None)

    for round_number in range(1, len(players)):
        create_online_round(tournament, players, round_number)
        players.insert(1, players.pop())


def create_online_round(tournament, players, round_number):
    round = Round.objects.create(
        tournament=tournament,
        round_number=round_number,
        type=Round.ONLINE
    )

    for i in range(len(players) // 2):
        player1 = players[i]
        player2 = players[len(players) - 1 - i]
        if player1 is not None and player2 is not None:
            game_utils.create(
                player1=player1,
                player2=player2,
                type=Game.ONLINE,
                status=Game.SCHEDULED,
                tournament=tournament,
                round=round,
            )


def get_next_round(tournament_id):
    lock.acquire('tournament')

    try:
        with transaction.atomic():
            tournament = Tournament.objects.get(
                id=tournament_id
            )
            tournament.current_round_number += 1
            round = tournament.get_current_round()
            tournament.save()
            return round, tournament.current_round_number

    except Exception as e:
        logger.error(
            f'Error getting next round for tournament '
            f'(ID: {tournament_id}) [{e}]'
        )
        raise

    finally:
        lock.release('tournament')


def start_next_round(tournament_id):
    try:
        next_round, round_number = get_next_round(tournament_id)
        if next_round is None:
            end(tournament_id)
        elif next_round.type == Round.ONLINE:
            notify_players(next_round, round_number)

    except Exception as e:
        logger.error(
            f'Error starting next tournament round '
            f'(ID: {tournament_id}) [{e}]'
        )


def notify_players(round, round_number):
    logger.info(
        f'Starting round {round_number} of '
        f'tournament "{round.tournament.name}" '
        f'(ID: {round.tournament.id})'
    )

    try:
        for game in round.games.all():
            game_utils.update(game.id, status=Game.IN_PROGRESS)
            game_utils.request_game_start(game.id)
            channels_utils.send_game_start(game)

    except Exception as e:
        logger.error(
            f'Error notifying players for round {round_number} '
            f'of tournament \'{round.tournament.name}\' '
            f'(ID: {round.tournament.id}) [{e}]'
        )


def advance(tournament):
    lock.acquire('game')

    try:
        if all(game.status == Game.FINISHED for game in
                tournament.get_current_round().games.all()):
            lock.release('game')
            start_next_round(tournament.id)
        else:
            lock.release('game')

    except Exception as e:
        logger.error(
            f'Error advancing tournament: '
            f'\'{tournament.name}\' (ID: {tournament.id}) [{e}]'
        )


def end(tournament_id):
    lock.acquire('tournament')

    try:
        with transaction.atomic():
            tournament = Tournament.objects.get(
                id=tournament_id
            )
            tournament.current_round_number = 0
            tournament.status = Tournament.FINISHED
            tournament.save()
            channels_utils.send_tournament_end(tournament)
            logger.info(
                f'Tournament \'{tournament.name}\' '
                f'(ID: {tournament.id}) has been won by '
                f'player \'{tournament.get_winner()}\''
            )

    except Exception as e:
        logger.error(
            f'Error ending tournament (ID: {tournament_id}) [{e}]'
        )

    finally:
        lock.release('tournament')


def get_my_tournaments(player_name, status=None):
    if not player_name:
        raise ValueError('No player name found, is the JWT cookie set?')

    try:
        player = Player.objects.get(name=player_name)

        my_tournaments = Tournament.objects.filter(
            players=player
        )

        if status:
            valid_statuses = [
                status for status, _ in Tournament.TOURNAMENT_STATUSES
            ]
            if status not in valid_statuses:
                raise ValueError(
                    f'Invalid status \'{status}\', must be one of '
                    f'{valid_statuses}'
                )
            my_tournaments = my_tournaments.filter(
                status=status
            )

        return my_tournaments.values()

    except Exception as e:
        raise Exception(
            f'Failed to get tournaments for player \'{player_name}\' [{e}]'
        )


def update_leaderboard(game):
    lock.acquire('tournament')

    try:
        with transaction.atomic():
            for player in [game.player1_name, game.player2_name]:
                entry = LeaderboardEntry.objects.filter(
                    player_name=player, tournament=game.tournament
                ).first()
                entry.games_played += 1
                if player == game.get_winner():
                    entry.games_won += 1
                    entry.points += 3
                entry.goals_for += game.get_score(player)
                entry.goals_against += game.get_score(
                    game.get_opponent(player)
                )
                entry.save()

    except Exception as e:
        logger.error(
            f'Failed to update leaderboard for tournament '
            f'(ID: {game.tournament.id}) '
            f'after game \'{game.get_name()}\' [{e}]'
        )

    finally:
        lock.release('tournament')


def get(filters):
    status = filters.get('status')
    type = filters.get('type')
    limit = filters.get('limit')

    tournaments = Tournament.objects.all()
    tournaments = tournaments.filter(status=status) if status else tournaments
    tournaments = tournaments.filter(type=type) if type else tournaments
    tournaments = tournaments[:int(limit)] if limit else tournaments
    tournament_list = [tournament.to_dict() for tournament in tournaments]
    return tournament_list
