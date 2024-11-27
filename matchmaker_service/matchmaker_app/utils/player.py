import logging

from django.db import transaction
from django.db.models import Q, F, Sum
from django.db.models.functions import Coalesce

from .. import lock
from ..models import Player, Game
from . import game as game_utils


logger = logging.getLogger('matchmaker-service')


def get_or_create(player_name):
    lock.acquire('player')

    try:
        player, created = Player.objects.\
                    get_or_create(name=player_name)
        if created:
            logger.info(f'Created player: \'{player_name}\'')
        return player, created

    except Exception as e:
        raise Exception(f'Error creating player {player_name} [{e}]')

    finally:
        lock.release('player')


def update(player_name, **kwargs):
    lock.acquire('player', 'game')
    name_changed = False
    new_name = None

    try:
        player = Player.objects.get(name=player_name)

        if 'name' in kwargs and kwargs['name'] != player.name:
            name_changed = True
            new_name = kwargs['name']

        with transaction.atomic():
            for key, value in kwargs.items():
                setattr(player, key, value)
            player.save()

            if name_changed:
                player.refresh_from_db()
                game_utils.update_player_names(player)
                logger.debug(
                    f'Updated games to reflect player name change '
                    f'(Old name: \'{player_name}\' | '
                    f'New name: \'{new_name}\') '
                )

        logger.debug(f'Updated player \'{player_name}\' [{kwargs}]')

        return player

    except Exception as e:
        raise Exception(f'Error updating player {player_name} [{e}]')

    finally:
        lock.release('player', 'game')


def get_stats(
        player_name,
        opponent_name=None,
        position=None,
        status=None,
        limit=None
):
    lock.acquire('player', 'game')

    try:
        player = Player.objects.get(name=player_name)
        if not player:
            raise Exception(f'Player \'${player_name}\' not found')

        games = filter_games(player, opponent_name, position, status, limit)
        total_finished_games = sum(
            1 for game in games if game.status == Game.FINISHED
        )
        total_wins = sum(
            1 for game in games if game.get_winner() == player_name
        )
        total_losses = total_finished_games - total_wins

        goals_for = games.aggregate(
            goals_for=Sum(
                F('player1_score') if position in ['home', 'left']
                else F('player2_score')
            )
        )['goals_for'] or 0
        goals_against = games.aggregate(
            goals_against=Sum(
                F('player2_score') if position in ['home', 'left']
                else F('player1_score')
            )
        )['goals_against'] or 0

        win_rate = (
            total_wins / total_finished_games * 100
        ) if total_finished_games > 0 else 0

        games_list = []
        for game in games:
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

        return {
            'win_rate': win_rate,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'games': games_list
        }

    except Exception as e:
        raise Exception(f'Error getting stats for player {player_name} [{e}]')

    finally:
        lock.release('player', 'game')


def filter_games(player, opponent_name, position, status, limit):
    games = Game.objects.filter(
        Q(player1=player) | Q(player2=player)
    )

    if opponent_name:
        opponent = Player.objects.filter(name=opponent_name).first()
        if not opponent:
            raise Exception(f'Opponent \'${opponent_name}\' not found')

        games = games.filter(
            Q(player1=opponent) | Q(player2=opponent)
        )

    if position:
        if position in ['home', 'left']:
            games = games.filter(player1=player)
        elif position in ['away', 'right']:
            games = games.filter(player2=player)
        else:
            raise Exception(
                f'Position \'${position}\' not found '
                f'in [home, left, away, right]'
            )

    if status:
        if status in dict(Game.GAME_STATUSES):
            games = games.filter(status=status)
        else:
            raise Exception(
                f'Status \'${status}\' not found '
                f'in {dict(Game.GAME_STATUSES)}'
            )

    if limit:
        try:
            limit = int(limit)
            games = games.order_by(
                Coalesce(F('finished_at'), F('created_at')).desc()
            )[:limit]
        except Exception:
            raise Exception(f"Invalid limit value '${limit}'")

    return games
