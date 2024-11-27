import json

from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from matchmaker_app.utils.decorators import jwt_required
from matchmaker_service.utils.decorators import handle_exceptions, log_request
from matchmaker_service.utils.mixins import MethodNotAllowedMixin
from ..models import Tournament
from ..utils import tournament as tournament_utils


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class TournamentsView(MethodNotAllowedMixin, View):
    # GET  /api/tournaments/  : List all tournaments
    #                         ?status=<tournament_status>  # Optional
    #                         ?type=<tournament_type>      # Optional
    #                         ?limit=<last_n_tournaments>  # Optional
    # POST /api/tournaments/  : Create a new tournament
    #                         {tournament_name, pool_size, players, type}

    def get(self, request, *args, **kwargs):
        filters = {
            'status': request.GET.get('status'),
            'type': request.GET.get('type'),
            'limit': request.GET.get('limit')
        }

        tournament_list = tournament_utils.get(filters)
        return JsonResponse(
            {'tournaments': tournament_list},
            json_dumps_params={'indent': 4}
        )

    @method_decorator(jwt_required)
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        pool_size = data.get('pool_size')
        tournament_name = data.get('tournament_name')
        players = data.get('players', [])
        tournament_type = data.get('type', Tournament.ONLINE)

        if not isinstance(players, list):
            players = [players]
        if tournament_type != Tournament.LOCAL:
            players.append(request.jwt_username)

        tournament_id = tournament_utils.registration(
            pool_size, tournament_name, players, tournament_type
        )
        tournament_url = (
            f'/matchmaker-service'
            f'{reverse("tournaments-detail", args=[tournament_id])}'
        )
        tournament_details = Tournament.objects.get(id=tournament_id)

        return JsonResponse(
            {
                'message': 'Tournament created successfully',
                'tournament_id': tournament_id,
                'tournament_url': (
                    request.build_absolute_uri(tournament_url).rstrip('/')
                ),
                'tournament_details': tournament_details.to_dict()
            }, status=201
        )


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class MyTournamentsView(MethodNotAllowedMixin, View):
    # GET /api/tournaments/me/ : List all tournaments of the player
    #                            (requires JWT cookie)
    #                            ?status=<tournament_status>  # Optional

    @method_decorator(jwt_required)
    def get(self, request, *args, **kwargs):
        player_name = request.jwt_username
        status = request.GET.get('status')

        my_tournaments = tournament_utils.get_my_tournaments(
            player_name, status
        )

        return JsonResponse(
            {'tournaments': list(my_tournaments)},
            json_dumps_params={'indent': 4}
        )


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class TournamentDetailView(MethodNotAllowedMixin, View):
    # GET /api/tournaments/<tournament_id>/ : Get details of a tournament
    # POST /api/tournaments/<tournament_id>/ : Join a tournament {player}
    # DELETE /api/tournaments/<tournament_id>/ : Leave a tournament {player}

    def get(self, request, *args, **kwargs):
        tournament_id = kwargs.get('tournament_id')

        tournament = Tournament.objects.get(id=tournament_id)
        return JsonResponse(
            tournament.to_dict(), json_dumps_params={'indent': 4}
        )

    @method_decorator(jwt_required)
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        data = {}
        if request.body:
            data = json.loads(request.body)

        tournament_id = kwargs.get('tournament_id')
        tournament = Tournament.objects.get(id=tournament_id)
        tournament_type = tournament.type

        player_name = data.get('player') \
            if tournament_type == Tournament.LOCAL \
            else request.jwt_username

        tournament_utils.join(tournament_id, player_name)

        return JsonResponse(
            {'message': 'Tournament joined successfully'},
            status=200
        )

    @method_decorator(jwt_required)
    @method_decorator(csrf_protect)
    def delete(self, request, *args, **kwargs):
        data = {}
        if request.body:
            data = json.loads(request.body)

        tournament_id = kwargs.get('tournament_id')
        tournament = Tournament.objects.get(id=tournament_id)
        tournament_type = tournament.type

        player_name = data.get('player') \
            if tournament_type == Tournament.LOCAL \
            else request.jwt_username

        tournament_utils.leave(tournament_id, player_name, tournament_type)

        return JsonResponse(
            {'message': 'Tournament left successfully'},
            status=200
        )
