import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


logger = logging.getLogger('matchmaker-service')


def send_message(player, message_type, **kwargs):
    try:
        channel_layer = get_channel_layer()
        message = {
            'type': message_type,
            **kwargs
        }

        if player.channel_name:
            logger.info(
                f'Sending message to {player} '
                f'(type: {message_type})'
            )
            async_to_sync(channel_layer.send)(
                player.channel_name,
                message
            )
        else:
            player.add_message(message)
            logger.warning(
                f'Failed to send message to {player} '
                f'(type: {message_type}) '
                f'[Player is offline]'
            )

    except Exception as e:
        raise Exception(
            f'Failed to send message to {player} '
            f'(type: {message_type}) '
            f'[{e}]'
        )


def send_game_start(game):
    game.refresh_from_db()

    logger.debug(
        f'Sending game_start message to players '
        f'in game \'{game.get_name()}\' (ID: {game.id})'
    )
    game_details = game.to_dict()
    for player, opponent in [
        (game.player1, game.player2),
        (game.player2, game.player1)
    ]:
        player.refresh_from_db()
        send_message(
            player,
            'game_start',
            game_id=str(game.id),
            player_position=game.get_player_position(player.name),
            opponent_name=opponent.name,
            game_details=game_details
        )


def send_challenge(opponent, player, game):
    game_details = game.to_dict()
    send_message(
        opponent,
        'challenge',
        opponent_name=player.name,
        game_id=game.id,
        game_details=game_details
    )


def send_tournament_start(tournament):
    tournament.refresh_from_db()

    logger.debug(
        f'Sending tournament_start message to players '
        f'in tournament \'{tournament.name}\' (ID: {tournament.id})'
    )
    tournament_details = tournament.to_dict()
    for player in tournament.players.all():
        player.refresh_from_db()
        send_message(
            player,
            'tournament_start',
            tournament_id=str(tournament.id),
            tournament_details=tournament_details
        )


def send_tournament_end(tournament):
    tournament.refresh_from_db()

    logger.debug(
        f'Sending tournament_end message to players '
        f'in tournament \'{tournament.name}\' (ID: {tournament.id})'
    )
    tournament_details = tournament.to_dict()
    for player in tournament.players.all():
        player.refresh_from_db()
        send_message(
            player,
            'tournament_end',
            tournament_id=str(tournament.id),
            tournament_details=tournament_details
        )


def send_tournament_update(tournament):
    tournament.refresh_from_db()

    logger.debug(
        f'Sending tournament_update message to players '
        f'in tournament \'{tournament.name}\' (ID: {tournament.id})'
    )
    tournament_details = tournament.to_dict()
    for player in tournament.players.all():
        player.refresh_from_db()
        send_message(
            player,
            'tournament_update',
            tournament_id=str(tournament.id),
            tournament_details=tournament_details
        )
