import json
import logging
import uuid

from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

from .consumers import GamePlayerConsumer
from game_service.utils.decorators import log_request, handle_exceptions
from game_service.utils.mixins import MethodNotAllowedMixin


logger = logging.getLogger('game-service')


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class Game(MethodNotAllowedMixin, View):
    # PUT   /api/game/<str:game_id>/    : Create a game
    # GET   /api/game/<str:game_id>/    : Get a game's current state

    def put(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')
        async_to_sync(GamePlayerConsumer.create_game)(game_id)
        game = GamePlayerConsumer.get_game(game_id)
        if game.status != 'created':
            return JsonResponse(
                {'message': f'Game {game_id} already existing'}, status=500
            )

        return JsonResponse(
            {'message': f'Game {game_id} created successfully'}, status=200
        )

    def get(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')
        game = GamePlayerConsumer.get_game(game_id)
        if not game:
            return JsonResponse(
                {'message': f'Game {game_id} not existing'}, status=500
            )

        return JsonResponse(
            game.generate_message('update_message'),
            json_dumps_params={'indent': 4}
        )


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class Start(MethodNotAllowedMixin, View):
    # PUT   /api/start/<str:game_id>/   : Start a game

    def put(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')
        game = GamePlayerConsumer.get_game(game_id)
        if not game:
            return JsonResponse(
                {'message': f'Game {game_id} not existing'}, status=500
            )
        elif game.status != 'created':
            return JsonResponse(
                {'message': f'Game {game_id} already started'}, status=500
            )

        async_to_sync(game.start)()
        return JsonResponse(
            {'message': f'Game {game_id} started successfully'}, status=200
        )


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class Join(MethodNotAllowedMixin, View):
    # PUT   /api/join/<str:game_id>/        : Add a player to a game
    #                                       {
    #                                           "side": str,    # Required
    #                                       }

    def put(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')
        game = GamePlayerConsumer.get_game(game_id)
        if not game:
            return JsonResponse(
                {'message': f'Game {game_id} not existing'}, status=500
            )
        elif game.status == 'created':
            return JsonResponse(
                {'message': f'Game {game_id} not open yet'}, status=500
            )
        elif game.status != 'waiting_for_players':
            return JsonResponse(
                {'message': f'Game {game_id} already started'}, status=500
            )

        data = json.loads(request.body)
        side = data.get('side')
        if side not in ['left', 'right']:
            return JsonResponse(
                {'message': 'side must be \'left\' or \'right\''},
                status=500
            )
        elif side in game.player:
            return JsonResponse(
                {'message': f'{side} player joined game {game_id} yet'},
                status=500
            )
        else:
            game.add_player(
                str(uuid.uuid4()),
                side,
                'ArrowUp',
                'ArrowDown'
            )
            return JsonResponse(
                {'message': f'{side} player added to game {game_id}'},
                status=200
            )


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class Control(MethodNotAllowedMixin, View):
    # PUT  /api/control/<str:game_id>/     : Send control message
    #                                       {
    #                                           "side": str,    # Required
    #                                           "key": str      # Required
    #                                           "event": str,   # Required
    #                                       }

    def put(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')
        game = GamePlayerConsumer.get_game(game_id)
        if not game:
            return JsonResponse(
                {'message': f'Game {game_id} not existing'}, status=500
            )
        elif game.status != 'game_started':
            return JsonResponse(
                {'message': f'Game {game_id} not started'}, status=500
            )

        data = json.loads(request.body)
        side = data.get('side')
        key = data.get('key')
        event = data.get('event')
        if side not in game.player:
            return JsonResponse(
                {'message': 'error in \'side\' parameter'},
                status=500
            )
        else:
            player = game.player[side]
            keyname = player.key_to_action.get(key, '')
            suffix = '_off' if event == 'keyup' else ''
            game.game_logic.trigger_move(side, keyname + suffix)
            return JsonResponse(
                {'message': 'Key event registered successfully'},
                status=200
            )


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class getCsrfToken(MethodNotAllowedMixin, View):
    # GET /get-csrf-token/ : Returns CSRF token

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        csrf_token = request.META.get('CSRF_COOKIE', '')
        return JsonResponse({'csrfToken': csrf_token})


@method_decorator(handle_exceptions, name='dispatch')
class HealthCheck(MethodNotAllowedMixin, View):
    # GET /health/ : Returns status ok

    def get(self, request):
        return JsonResponse({'status': 'ok'})
