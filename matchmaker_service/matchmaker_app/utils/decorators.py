import json
import logging
from functools import wraps

from django.conf import settings
from django.http import JsonResponse

from matchmaker_app.models import Game, Tournament
from matchmaker_app.utils.jwt import validate as jwt_validate


logger = logging.getLogger('matchmaker-service')


def jwt_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        data = {}
        if request.body:
            data = json.loads(request.body)

        game_type = data.get('type')
        if game_type == Game.LOCAL or game_type == Tournament.LOCAL:
            return view_func(request, *args, **kwargs)

        response = jwt_validate(request)
        if response.status_code != 200:
            logger.error(
                f'{request.method} {request.path} - '
                f'Error: \'Invalid or missing JWT token\''
            )
            return JsonResponse(
                {'error': 'Invalid or missing JWT token'}, status=403
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def api_key_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != settings.MATCHMAKER_SERVICE_API_KEY:
            logger.error(
                f'{request.method} {request.path} - '
                f'Error: \'Invalid or missing API key\''
            )
            return JsonResponse(
                {'error': 'Invalid or missing API key'}, status=403
            )
        return view_func(request, *args, **kwargs)
    return wrapper
