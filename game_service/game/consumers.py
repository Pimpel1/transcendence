import asyncio
import http.client
import json
import logging
import logging.config
import ssl
import time
import urllib.parse
import uuid

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from .game import GameLogic


PITCH_WIDTH = 480       # Pixels
PITCH_HEIGHT = 360      # Pixels
BALL_SIZE = 5           # Pixels
BALL_MOVES = 200        # Pixels per second
ACCELERATOR = 15        # Pixels per second
MAX_ACCELERATION = 500  # Pixels per second
START_AMPLITUDE = 60    # Degrees
PADDLE_SIZE = 60        # Pixels
PADDLE_MOVES = 300      # Pixels per second
PADDLE_AMPLITUDE = 60   # Degrees
PAUSE_TIME = 1.5        # Seconds
UPDATE_TIME = 0.03      # Seconds
FORFEIT_TIME = int(settings.GAME_CONNECTION_TIMEOUT)
MAX_POINTS = 3

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('game-service')


class GamePlayerConsumer(AsyncWebsocketConsumer):

    participants = {}
    games = {}
    games_lock = asyncio.Lock()
    clean_loop_started = asyncio.Event()

    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs'].get('game_id')
        query_string = self.scope['query_string'].decode()
        params = urllib.parse.parse_qs(query_string)
        player_side = params.get('position', [''])[0]
        up_key = params.get('up', ['ArrowUp'])[0]
        down_key = params.get('down', ['ArrowDown'])[0]

        game = self.get_game(self.game_id)
        if not game:
            return
        await self.add_participant(game, player_side, up_key, down_key)

    @classmethod
    async def create_game(cls, game_id):
        await cls.start_clean_loop()
        if game_id not in cls.games:
            cls.games[game_id] = Game(game_id)
            logger.debug(f'Game created for game_id {game_id}')
        else:
            logger.debug(f'Game {game_id} already exists')

    async def add_participant(self, game, player_side, up_key, down_key):
        self.id = str(uuid.uuid4())
        game.add_player(
            self.id,
            player_side,
            up_key,
            down_key,
            self.channel_layer,
            self.channel_name)
        logger.info(
            f'{player_side} player connected to game (ID: {self.game_id}) '
            f'with {up_key} for up and {down_key} for down '
            f'[{self.scope["client"][0]}:{self.scope["client"][1]}]'
        )

        self.group_name = f'game_{self.game_id}'
        await self.accept()
        await self.channel_layer.group_add(
            self.group_name, self.channel_name
        )

    async def disconnect(self, close_code):
        logger.info(
            f'Player disconnected from game (ID: {self.game_id}) '
            f'[{self.scope["client"][0]}:{self.scope["client"][1]}] '
            f'[{close_code}]'
        )

        await self.channel_layer.group_discard(
            self.group_name, self.channel_name
        )

        if self.game_id in self.games:
            self.games[self.game_id].disconnect_player(self.id)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        await self.channel_layer.group_send(
            self.group_name, {
                'type': text_data_json['messageType'],
                'id': self.id,
                **text_data_json
            }
        )

    # Handle message from websocket
    @classmethod
    async def key_event_message(self, event):
        for game_id in self.games:
            self.games[game_id].key_event(event)

    async def connection_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def initial_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def update_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def endgame_message(self, event):
        await self.send(text_data=json.dumps(event))

    @classmethod
    async def start_clean_loop(cls):
        if not cls.clean_loop_started.is_set():
            cls.clean_loop_started.set()
            asyncio.create_task(cls.clean_loop())
        else:
            return

    @classmethod
    async def clean_loop(cls):
        while True:
            games_to_suppress = []
            for game_id in cls.games:
                game = cls.games[game_id]
                if (game.status == 'game_ended'):
                    games_to_suppress.append(game_id)
            for game_id in games_to_suppress:
                del cls.games[game_id]
                logger.debug(f'Deleted game {game_id}')
            await asyncio.sleep(1)

    @classmethod
    def get_game(cls, game_id):
        if game_id in cls.games:
            return cls.games[game_id]
        else:
            return None


class Game:

    def __init__(
        self,
        id
    ):
        self.id = id
        self.player = {}
        self.game_logic = None
        self.status = 'created'
        self.player_lock = asyncio.Lock()

    async def notify_players(self, message):
        async with self.player_lock:
            for side in self.player:
                player = self.player[side]
                if player.channel_layer and player.channel:
                    await player.channel_layer.send(
                        player.channel,
                        message
                    )

    def add_player(
        self,
        id,
        player_side,
        up_key,
        down_key,
        channel_layer=None,
        channel=None
    ):
        if player_side in ['left', 'right'] and player_side not in self.player:
            self.player[player_side] = Participant(
                id,
                player_side,
                up_key,
                down_key,
                channel_layer,
                channel
            )
            GamePlayerConsumer.participants[id] = self.player[player_side]

    def disconnect_player(self, player_id):
        for side in list(self.player.keys()):
            if player_id == self.player[side].id:
                del self.player[side]
                self.status = f'{side}_player_disconnected'

    async def start(self):
        self.status = 'waiting_for_players'
        self.start_time = time.time()
        asyncio.create_task(self.loop())

    async def loop(self):
        while self.status == 'waiting_for_players':
            await self.wait()
        while self.status == 'game_started':
            await self.update()
        await self.end()

    async def wait(self):
        if time.time() - self.start_time >= FORFEIT_TIME:
            self.status = 'player_forfeited'
            return
        if not ('left' in self.player and 'right' in self.player):
            await asyncio.sleep(UPDATE_TIME * 0.01)
            return
        await self.notify_players(self.generate_init_message())
        self.game_logic = GameLogic(
            PITCH_WIDTH,
            PITCH_HEIGHT,
            BALL_SIZE,
            BALL_MOVES,
            START_AMPLITUDE,
            PADDLE_SIZE,
            PADDLE_MOVES,
            PADDLE_AMPLITUDE,
            PAUSE_TIME,
            MAX_POINTS,
            ACCELERATOR,
            MAX_ACCELERATION
        )
        self.game_logic.start()
        self.status = 'game_started'
        self.last_update = time.time() - UPDATE_TIME

    async def update(self):
        sleep_time = UPDATE_TIME - (time.time() - self.last_update)
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
        self.last_update = time.time()
        self.game_logic.update()
        try:
            await self.notify_players(self.generate_message('update_message'))
        except Exception as e:
            logger.error(f'Failed to notify players [{e}]')
        if self.game_logic.finished:
            self.status = 'game_over'

    async def end(self):
        await self.submit_result()
        await self.notify_players(self.generate_message('endgame_message'))
        for side in list(self.player.keys()):
            del self.player[side]
        self.status = 'game_ended'

    async def get_matchmaker_csrf_token(self):
        context = ssl._create_unverified_context()
        conn = http.client.HTTPSConnection(
            'matchmaker-service',
            8002,
            context=context
        )

        try:
            await sync_to_async(conn.request)('GET', '/get-csrf-token/')
            response = await sync_to_async(conn.getresponse)()

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
                    'Failed to get CSRF token from matchmaker-service'
                    f' {response.status} {response.reason}'
                )
        except Exception as e:
            logger.error(f'{e}')
        finally:
            await sync_to_async(conn.close)()
        return None

    async def submit_result(self):
        csrf_token, cookies = await self.get_matchmaker_csrf_token()

        if not csrf_token or not cookies:
            logger.error(
                f'Failed to submit result of game {self.id}'
                ' [No CSRF token or cookie]'
            )
            return

        context = ssl._create_unverified_context()
        conn = http.client.HTTPSConnection(
            'matchmaker-service',
            8002,
            context=context
        )
        left_score = 0
        right_score = 0
        if 'left' not in self.player and 'right' in self.player:
            right_score = 3
        elif 'right' not in self.player and 'left' in self.player:
            left_score = 3
        elif self.game_logic:
            left_score = self.game_logic.player['left'].score
            right_score = self.game_logic.player['right'].score

        payload = json.dumps({
            'game_id': self.id,
            'left_score': left_score,
            'right_score': right_score,
            'status': self.status
        })

        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
            'X-API-Key': settings.MATCHMAKER_SERVICE_API_KEY,
            'Referer': 'https://game-service:8001/',
            'Cookie': cookies
        }

        try:
            await sync_to_async(conn.request)(
                'POST',
                '/api/games/result/',
                body=payload,
                headers=headers
            )
            response = await sync_to_async(conn.getresponse)()

            if response.status != 200:
                logger.error(
                    f'Failed to submit result of game {self.id}'
                    f' {response.status} {response.reason}'
                )
        except Exception as e:
            logger.error(f'{e}')
        finally:
            await sync_to_async(conn.close)()

    def generate_init_message(self):
        return {
            'type': 'initial_message',
            'width': PITCH_WIDTH,
            'height': PITCH_HEIGHT,
            'paddleSize': PADDLE_SIZE,
            'ballSize': BALL_SIZE,
        }

    def generate_message(self, message_type):
        return {
            'type': message_type,
            'time': '-' if not self.game_logic
            else self.game_logic.chrono.get_time(),
            'ballX': '-' if not self.game_logic else self.game_logic.ball.left,
            'ballY': '-' if not self.game_logic else self.game_logic.ball.top,
            'paddleLeft': 'not connected'
            if 'left' not in self.player or not self.game_logic
            else self.game_logic.player['left'].paddle.top,
            'paddleRight': 'not connected'
            if 'right' not in self.player or not self.game_logic
            else self.game_logic.player['right'].paddle.top,
            'scoreLeft': '-'
            if 'left' not in self.player or not self.game_logic
            else self.game_logic.player['left'].score,
            'scoreRight': '-'
            if 'right' not in self.player or not self.game_logic
            else self.game_logic.player['right'].score,
            'status': self.status,
        }

    def key_event(self, event):
        player = None
        for side in self.player:
            if event['id'] == self.player[side].id:
                player = self.player[side]
        if not player:
            return
        key = event['key']
        keyname = player.key_to_action.get(key, '')
        side = player.side
        suffix = '_off' if event.get('event') == 'keyup' else ''
        if self.game_logic:
            self.game_logic.trigger_move(side, keyname + suffix)


class Participant:
    def __init__(
        self,
        id,
        side,
        key_up,
        key_down,
        channel_layer=None,
        channel=None
    ):
        self.id = id
        self.channel_layer = channel_layer
        self.channel = channel
        self.key_to_action = {
                key_up: 'up',
                key_down: 'down',
            }
        self.side = side
