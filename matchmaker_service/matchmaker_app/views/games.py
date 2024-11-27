import json
import logging

from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse

from matchmaker_app.utils.decorators import jwt_required, api_key_required
from matchmaker_service.utils.decorators import handle_exceptions, log_request
from matchmaker_service.utils.mixins import MethodNotAllowedMixin
from ..models import Game
from ..utils import game as game_utils
from ..utils import tournament as tournament_utils
from ..utils import channels as channels_utils


logger = logging.getLogger('matchmaker-service')


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class GamesView(MethodNotAllowedMixin, View):
    # GET  /api/games/  : List all games
    #                   ?status=<game_status>       # Optional
    #                   ?type=<game_type>           # Optional
    #                   ?player=<player_name>       # Optional
    #                   ?opponent=<opponent_name>   # Optional
    #                   ?joined=<bool>              # Optional
    #                   ?limit=<last_n_games>       # Optional
    # POST /api/games/  : Register a game {player1, player2, type}

    def get(self, request, *args, **kwargs):
        filters = {
            'status': request.GET.get('status'),
            'type': request.GET.get('type'),
            'player': request.GET.get('player'),
            'opponent': request.GET.get('opponent'),
            'joined': None if 'joined' not in request.GET else (
                request.GET.get('joined').lower == 'true'
            ),
            'limit': request.GET.get('limit')
        }

        games_list = game_utils.get(filters)
        return JsonResponse(
            {'games': games_list}, json_dumps_params={'indent': 4}
        )

    @method_decorator(jwt_required)
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        data = {}
        if request.body:
            data = json.loads(request.body)

        game_type = data.get('type', Game.ONLINE)

        player1 = data.get('player1') \
            if game_type == Game.LOCAL \
            else request.jwt_username
        player2 = data.get('player2')

        game_id = game_utils.registration(player1, player2, game_type)
        game = Game.objects.get(id=game_id)
        game_details = game.to_dict()
        game_url = (
            f'/matchmaker-service'
            f'{reverse("games-detail", args=[game_id])}'
        )

        return JsonResponse(
            {
                'message': 'Game registered successfully',
                'game_url': (
                    request.build_absolute_uri(game_url).rstrip('/')
                ),
                'game_details': game_details
            }, status=201
        )


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class MyGamesView(MethodNotAllowedMixin, View):
    # GET /api/games/me/ : List all games of the player
    #                    ?joined=<bool>         # Optional
    #                    ?status=<game_status>  # Optional

    @method_decorator(jwt_required)
    def get(self, request, *args, **kwargs):
        player_name = request.jwt_username
        joined = request.GET.get('joined')
        status = request.GET.get('status')

        my_games = game_utils.get_my_games(player_name, joined, status)

        return JsonResponse(
            {'games': my_games}, json_dumps_params={'indent': 4}
        )


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class GameDetailView(MethodNotAllowedMixin, View):
    # GET /api/games/<game_id>/ : get details of a game
    # PUT /api/games/<game_id>/ : join a game {player}
    # DELETE /api/games/<game_id>/ : delete a game

    def get(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')

        game = Game.objects.get(id=game_id)
        return JsonResponse(
            game.to_dict(), json_dumps_params={'indent': 4}
        )

    @method_decorator(jwt_required)
    @method_decorator(csrf_protect)
    def put(self, request, *args, **kwargs):
        data = {}
        if request.body:
            data = json.loads(request.body)

        game_id = kwargs.get('game_id')
        game = Game.objects.get(id=game_id)
        game_type = game.type

        player = data.get('player') \
            if game_type == Game.LOCAL \
            else request.jwt_username

        game_utils.join(game_id, player)
        return JsonResponse(
            {'message': 'Game joined successfully'},
            status=200
        )

    @method_decorator(jwt_required)
    @method_decorator(csrf_protect)
    def delete(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')
        game = Game.objects.get(id=game_id)

        if not (
            game.status == Game.WAITING_FOR_PLAYERS
                and (
                    game.player1.name == request.jwt_username
                    or game.player2.name == request.jwt_username
                )
        ):
            raise ValueError(
                'You can only delete games if you are one of the players, '
                'and the game must be in the \'waiting for opponent\' state'
            )

        game.delete()
        logger.info(
            f'Game \'{game.get_name()}\' (ID: {game_id}) '
            f'deleted by {request.jwt_username}'
        )
        return JsonResponse(
            {'message': 'Game deleted successfully'},
            status=200
        )


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class GameResultView(MethodNotAllowedMixin, View):
    # POST /api/games/result/  : Submit the result of a game
    #                           {game_id, left_score, right_score}

    @method_decorator(api_key_required)
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        game_id = data.get('game_id')
        game_utils.update(
            game_id,
            player1_score=data.get('left_score'),
            player2_score=data.get('right_score'),
            status=Game.FINISHED,
            finished_at=timezone.now()
        )

        game = Game.objects.get(id=game_id)
        logger.info(
            f'Game \'{game.get_name()}\' (ID: {game_id}) '
            f'ended in {game.get_winner()}\'s favor '
            f'({game.player1_score} - {game.player2_score})'
        )

        if game.tournament:
            tournament = game.tournament
            tournament_utils.update_leaderboard(game)
            tournament_utils.advance(tournament)
            channels_utils.send_tournament_update(tournament)
            logger.info(
                f'Tournament \'{tournament.name}\' '
                f' (ID: {tournament.id}) '
                f'updated ranking: {tournament.get_ranking()}'
            )

        return JsonResponse(game.to_dict())


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class GameStartView(MethodNotAllowedMixin, View):
    # PUT  /api/games/start/<game_id>/  : Request the start of a game from
    #                                       game-service

    @method_decorator(csrf_protect)
    def put(self, request, *args, **kwargs):
        game_id = kwargs.get('game_id')
        game_utils.request_game_start(game_id)
        return JsonResponse(
            {'message': 'Game created successfully'},
            status=200
        )
