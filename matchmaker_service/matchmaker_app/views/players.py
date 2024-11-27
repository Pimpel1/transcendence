import json
import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from matchmaker_app.utils.decorators import api_key_required
from matchmaker_service.utils.decorators import handle_exceptions, log_request
from matchmaker_service.utils.mixins import MethodNotAllowedMixin
from ..models import Player
from ..utils import player as player_utils


logger = logging.getLogger('matchmaker-service')


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class PlayersView(MethodNotAllowedMixin, View):
    # GET /api/players/ : List all players
    # POST /api/players/ : Register a player
    #                      {name} required

    def get(self, request, *args, **kwargs):
        players = Player.objects.all()
        players_list = [player.to_dict() for player in players]
        return JsonResponse(
            {'players': players_list}, json_dumps_params={'indent': 4}
        )

    @method_decorator(api_key_required)
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        player_name = data.get('name')
        _, created = player_utils.get_or_create(player_name)
        if not created:
            logger.warning(f'Player already exists: {player_name}')
            return JsonResponse(
                {'error': 'Player already exists'}, status=400
            )
        return JsonResponse(
            {'message': 'Player created successfully'}, status=201
        )


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class PlayerDetailView(MethodNotAllowedMixin, View):
    # GET /api/players/<player_name>/   : Get details of a player
    # PATCH /api/players/<player_name>/ : Update a player
    #                                   {<field>: <value>} - one or more

    def get(self, request, *args, **kwargs):
        player_name = kwargs.get('player_name')

        player = Player.objects.get(name=player_name)
        return JsonResponse(
            player.to_dict(), json_dumps_params={'indent': 4}
        )

    @method_decorator(api_key_required)
    @method_decorator(csrf_protect)
    def patch(self, request, *args, **kwargs):
        player_name = kwargs.get('player_name')

        try:
            data = json.loads(request.body)
            player = Player.objects.get(name=player_name)
            player_utils.update(player_name, **data)
            return JsonResponse(player.to_dict())

        except Player.DoesNotExist:
            logger.warning(
                f'PATCH /api/players/{player_name}/ '
                f'[Player not found] ... creating player'
            )
            player, _ = player_utils.get_or_create(player_name)
            return JsonResponse(player.to_dict())


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class PlayerStatsView(MethodNotAllowedMixin, View):
    # GET /api/players/<player_name>/stats/ : Get game details and stats
    #                                         ?opponent=<opponent_name>
    #                                         ?position=<player_position>
    #                                         ?status=<game_status>
    #                                         ?limit=<last_n_games>

    def get(self, request, *args, **kwargs):
        player_name = kwargs.get('player_name')
        opponent_name = request.GET.get('opponent')
        player_position = request.GET.get('position')
        game_status = request.GET.get('status')
        limit = request.GET.get('limit')

        stats = player_utils.get_stats(
            player_name, opponent_name, player_position, game_status, limit
        )

        return JsonResponse(
            {'stats': stats}, json_dumps_params={'indent': 4}
        )
