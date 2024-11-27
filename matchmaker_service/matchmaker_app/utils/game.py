import http.client
import json
import logging
import ssl

from django.db import transaction
from django.db.models import Q

from ..models import Game, Player
from .. import lock
from . import channels as channels_utils
from . import player as player_utils


logger = logging.getLogger('matchmaker-service')


def create(
    player1,
    player2=None,
    type=Game.ONLINE,
    status=Game.WAITING_FOR_PLAYERS,
    tournament=None,
    round=None
):
    if isinstance(player1, str) and len(player1) == 0:
        player1 = None
    if player1 is None:
        raise Exception('Error creating game: No player1 was provided')

    lock.acquire('game')

    try:
        if type == Game.ONLINE:
            game = Game.objects.create(
                player1=player1,
                player2=player2,
                player1_name=player1.name if player1 else "*anyone*",
                player2_name=player2.name if player2 else "*anyone*",
                type=type,
                status=status,
                tournament=tournament,
                round=round
            )

        else:  # LOCAL game
            game = Game.objects.create(
                player1_name=player1,
                player2_name=player2,
                type=type,
                status=status,
                tournament=tournament,
                round=round
            )
        logger.info(
            f'Created {game.type} game '
            f'{game.id}'
        )
        request_game_create(game.id)
        return game

    except Exception as e:
        raise Exception(
            f'Error creating game '
            f'{game.id}:'
            f'[{e}]'
        )

    finally:
        lock.release('game')


def request_game_create(game_id):
    logger.debug(f'Creating Game Service game (ID: {game_id})')
    game_service_action(game_id, 'create')


def request_game_start(game_id):
    logger.debug(f'Start Game Service game (ID: {game_id})')
    game_service_action(game_id, 'start')


def game_service_action(game_id, action):
    page = 'game' if action == 'create' else action
    csrf_token, cookies = get_game_service_csrf_token()

    if not csrf_token or not cookies:
        logger.error(
            f'Failed to {action} game {game_id} '
            f'[No CSRF token or cookie]'
        )

    context = ssl._create_unverified_context()
    conn = http.client.HTTPSConnection(
        'game-service',
        8000,
        context=context
    )
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token,
        'Referer': 'https://game-service:8001/',
        'Cookie': cookies
    }

    try:
        conn.request(
            'PUT',
            f'/api/{page}/{game_id}/',
            headers=headers
        )
        response = conn.getresponse()
        if response.status != 200:
            logger.error(
                f'Failed to {action} game {game_id} '
                f'{response.status} {response.reason}'
            )
    except Exception as e:
        logger.error(f'{e}')
    finally:
        conn.close()


def get_game_service_csrf_token():
    context = ssl._create_unverified_context()
    conn = http.client.HTTPSConnection(
        'game-service',
        8000,
        context=context
    )

    try:
        conn.request('GET', '/get-csrf-token/')
        response = conn.getresponse()
        if response.status == 200:
            cookies = response.getheader('Set-Cookie')
            csrf_token = json.loads(
                response.read().decode('utf-8')
            )['csrfToken']
            if not csrf_token:
                raise Exception('No CSRF token found in response')
            return csrf_token, cookies
        else:
            raise Exception(
                f'Failed to get CSRF token from game-service '
                f'{response.status} {response.reason}'
            )
    except Exception as e:
        logger.error(f'{e}')
    finally:
        conn.close()
    return None


def update(game_id, **kwargs):
    lock.acquire('game')

    try:
        game = Game.objects.get(id=game_id)
        for key, value in kwargs.items():
            setattr(game, key, value)
        game.save()
        return game

    except Exception as e:
        raise Exception(f'Error updating game (ID: {game_id}) [{e}]')

    finally:
        lock.release('game')


def registration(player_name, opponent_name, type=Game.ONLINE):
    if opponent_name and len(opponent_name) == 0:
        opponent_name = None

    try:
        logger.debug(
            f'Registering {type} game \'{player_name} vs '
            f'{opponent_name if opponent_name else "*anyone*"}\''
        )

        if type != Game.ONLINE:
            return local_registration(player_name, opponent_name)

        player_names = [player_name]
        if opponent_name:
            player_names.append(opponent_name)

        players = {}
        for name in player_names:
            players[name], _ = player_utils.get_or_create(name)

        if opponent_name:
            game_id, game_ready = private_registration(
                players[player_name], players[opponent_name]
            )
        else:
            game_id, game_ready = open_registration(
                players[player_name]
            )

        if game_ready:
            with transaction.atomic():
                update(game_id, status=Game.IN_PROGRESS)
                channels_utils.send_game_start(Game.objects.get(id=game_id))
                logger.info(f'{player_name} joined game (ID: {game_id})')
                logger.info(
                    f'Started game '
                    f'\'{Game.objects.get(id=game_id).get_name()}\''
                    f' (ID: {game_id})'
                )

        return game_id

    except Exception as e:
        logger.error(
            f'Error registering game: '
            f'\'{player_name} vs '
            f'{opponent_name if opponent_name else "*anyone*"}\''
            f' [{e}]'
        )


def local_registration(player1_name, player2_name):
    try:
        with transaction.atomic():
            game = create(
                player1_name, player2_name, Game.LOCAL, Game.IN_PROGRESS
            )
            request_game_start(game.id)
            logger.info(
                f'Started local game: '
                f'\'{game.get_name()}\' (ID: {game.id})'
            )
            return game.id

    except Exception as e:
        raise Exception(
            f'Error creating local game '
            f'for {player1_name} and {player2_name} [{e}]'
        )


def private_registration(player, opponent):
    try:
        with transaction.atomic():
            game = Game.objects.filter(
                status=Game.WAITING_FOR_PLAYERS,
                player1__in=[player, opponent],
                player2__in=[None, player, opponent]
            ).first()
            if game:
                if game.player1 == player and game.player2 is None:
                    game.update(player2=opponent, player2_name=opponent.name)
                elif game.player1 == opponent and game.player2 is None:
                    game.update(player2=player, player2_name=player.name)
                elif game.player1 == player and game.player2 == opponent:
                    logger.warning(
                        f'Game \'{game.get_name()}\' (ID: {game.id}) '
                        f'already exists and is waiting for opponent'
                    )
                    return game.id, False
                game_ready = True
                request_game_start(game.id)
            else:
                game_ready = False
                game = create(
                    player, opponent, Game.ONLINE, Game.WAITING_FOR_PLAYERS
                )
                channels_utils.send_challenge(
                    opponent, player, game
                )
            return game.id, game_ready

    except Exception as e:
        raise Exception(
            f'Error creating or joining private game '
            f'for {player.name} and {opponent.name} [{e}]'
        )


def open_registration(player):
    try:
        with transaction.atomic():
            game = Game.objects.filter(
                status=Game.WAITING_FOR_PLAYERS,
                player2__isnull=True
            ).first()
            if game:
                update(game.id, player2=player, player2_name=player.name)
                game_ready = True
            else:
                game_ready = False
                game = create(
                    player, None, Game.ONLINE, Game.WAITING_FOR_PLAYERS
                )
                request_game_start(game.id)
            return game.id, game_ready

    except Exception as e:
        raise Exception(
            f'Error creating or joining open game '
            f'for {player.name} [{e}]'
        )


def join(game_id, player_name):
    player, _ = player_utils.get_or_create(player_name)

    lock.acquire('game')

    try:
        with transaction.atomic():
            game = Game.objects.get(id=game_id)

            if game.status != Game.WAITING_FOR_PLAYERS:
                if player == game.player1 or player == game.player2:
                    raise Exception(
                        f'Player \'{player_name}\' is already in game '
                        f'(ID: {game_id})'
                    )
                else:
                    raise Exception(
                        f'Game \'{game.get_name()}\' (ID: {game_id}) '
                        f'is not accepting players (pool is full)'
                    )

            if game.player2 is None:
                game.player2 = player
            game.status = Game.IN_PROGRESS
            game.save()
            channels_utils.send_game_start(game)
            logger.info(f'{player_name} joined game (ID: {game_id})')
            logger.info(
                f'Started {game.type} game '
                f'\'{game.get_name()}\' (ID: {game_id})'
            )

    finally:
        lock.release('game')


def update_player_names(player):
    Game.objects.filter(player1=player).update(player1_name=player.name)
    Game.objects.filter(player2=player).update(player2_name=player.name)


def get_my_games(player_name, joined=None, status=None):
    if not player_name:
        raise ValueError('No player name found, is the JWT cookie set?')

    try:
        player = Player.objects.get(name=player_name)

        my_games = Game.objects.filter(
            Q(player1=player) | Q(player2=player)
        )

        if joined is not None:
            if joined.lower() not in ['true', 'false']:
                raise ValueError(
                    'Invalid value for \'joined\' parameter '
                    '(expected \'true\', \'false\', or None)'
                )
            joined = joined.lower() == 'true'

            if joined:
                my_games = my_games.filter(
                    Q(player1=player) |
                    (Q(player2=player) & ~Q(status=Game.WAITING_FOR_PLAYERS))
                )
            else:
                my_games = my_games.filter(
                    Q(player2=player) & Q(status=Game.WAITING_FOR_PLAYERS)
                )

        if status is not None:
            valid_statuses = [status for status, _ in Game.GAME_STATUSES]
            if status in valid_statuses:
                my_games = my_games.filter(status=status)
            else:
                raise ValueError(
                    f'Invalid value for \'status\' parameter '
                    f'(expected one of: {valid_statuses})'
                )

        games_list = []
        for game in my_games:
            games_list.append({
                'id': game.id,
                'status': game.status,
                'player1_name': game.player1.name,
                'player2_name': game.player2.name,
                'player1_position': game.player1_position,
                'player2_position': game.player2_position,
                'player1_score': game.player1_score,
                'player2_score': game.player2_score,
                'winner_name': game.get_winner(),
                'date': game.finished_at or game.created_at,
            })

        return games_list

    except Exception as e:
        raise Exception(
            f"Failed to get games for player '{player_name}' [{e}]"
        )


def get(filters):
    status = filters.get('status')
    type = filters.get('type')
    player = filters.get('player')
    opponent = filters.get('opponent')
    joined = filters.get('joined')
    limit = filters.get('limit')

    games = Game.objects.all()
    games.filter(status=status) if status else games
    games.filter(type=type) if type else games
    games.filter(Q(player1=player) | Q(player2=player)) if player else games
    games.filter(Q(player1=opponent) | Q(player2=opponent)) \
        if opponent else games
    games.filter(
        Q(player1=player) |
        (
            Q(player2=player) &
            ~Q(status=Game.WAITING_FOR_PLAYERS)
        )
    ) if player and joined else games
    games.filter(Q(player2=player) & Q(status=Game.WAITING_FOR_PLAYERS)) \
        if player and joined is False else games
    games = games[:limit] if limit else games
    games_list = [game.to_dict() for game in games]
    return games_list
