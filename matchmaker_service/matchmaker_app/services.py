import logging

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer

from . import lock
from .utils import channels as channels_utils
from .utils import player as player


logger = logging.getLogger('matchmaker-service')


class MatchmakingService:
    def __init__(self, player_name, channel_name):
        self.player_name = player_name
        self.channel_name = channel_name
        self.player = None
        self.channel_layer = get_channel_layer()

    async def send_queued_messages(self):
        while True:
            try:
                await database_sync_to_async(self._send_queued_messages_sync)()
                break
            except Exception as e:
                logger.error(f'[Database error occurred [{e}] retrying ...')

    def _send_queued_messages_sync(self):
        lock.acquire('player')

        try:
            self.player.refresh_from_db()
            queued_messages = self.player.flush_messages()
            self.player.flush_messages()  # clear the queue

            for message in queued_messages:
                logger.debug(
                    f'Sending game (ID: {message["game_id"]}) to '
                    f'{self.player_name} [from queue]'
                )
                channels_utils.send_message(
                    self.player, message['type'], **message
                )

        except Exception as e:
            logger.error(
                f'Error sending queued messages to {self.player.name} [{e}]'
            )

        finally:
            lock.release('player')

    async def connect(self):
        self.player, _ = await database_sync_to_async(player.get_or_create)(
            self.player_name
        )
        await database_sync_to_async(player.update)(
            self.player_name, channel_name=self.channel_name
        )

    async def disconnect(self):
        await database_sync_to_async(player.update)(
            self.player_name, channel_name=None
        )
