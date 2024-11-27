import json
import logging
import logging.config
import urllib.parse

from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer

from .services import MatchmakingService
from .utils.jwt import get_username as jwt_get_username


logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('matchmaker-service')


class MatchmakerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            query_string = self.scope['query_string'].decode()
            jwt = self.scope['cookies'].get('jwt')

            if jwt:
                self.player_name = jwt_get_username(jwt)
            else:
                self.player_name = urllib.parse.unquote(
                    query_string.split('=')[1]
                )

            if not self.player_name:
                await self.close()
                return

            self.matchmaking_service = MatchmakingService(
                self.player_name, self.channel_name
            )
            await self.matchmaking_service.connect()

            logger.info(
                f'Player connected (Name: {self.player_name}) '
                f'[{self.scope["client"][0]}:{self.scope["client"][1]}]'
            )

            await self.accept()
            # await self.matchmaking_service.send_queued_messages()

        except Exception as e:
            logger.error(f'Error connecting player [{str(e)}]')
            await self.close()

    async def disconnect(self, close_code):
        logger.info(
            f'Player disconnected (Name: {self.player_name}) '
            f'[{self.scope["client"][0]}:{self.scope["client"][1]}] '
            f'[{close_code}]'
        )

        await self.matchmaking_service.disconnect()

    async def receive(self, text_data):
        pass

    async def game_start(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_start',
            'game_id': event['game_id'],
            'player_position': event['player_position'],
            'opponent_name': event['opponent_name'],
            'game_details': event['game_details']
        }))

    async def challenge(self, event):
        await self.send(text_data=json.dumps({
            'type': 'challenge',
            'opponent_name': event['opponent_name'],
            'game_id': event['game_id'],
            'game_details': event['game_details']
        }))

    async def tournament_start(self, event):
        await self.send(text_data=json.dumps({
            'type': 'tournament_start',
            'tournament_id': event['tournament_id'],
            'tournament_details': event['tournament_details']
        }))

    async def tournament_end(self, event):
        await self.send(text_data=json.dumps({
            'type': 'tournament_end',
            'tournament_id': event['tournament_id'],
            'tournament_details': event['tournament_details']
        }))

    async def tournament_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'tournament_update',
            'tournament_id': event['tournament_id'],
            'tournament_details': event['tournament_details']
        }))
