import logging
from django.http import JsonResponse


logger = logging.getLogger('game-service')


class MethodNotAllowedMixin:
    def http_method_not_allowed(self, request, *args, **kwargs):
        logger.warning(f'{request.method} {request.path} [Method not allowed]')
        return JsonResponse({'error': 'Method not allowed'}, status=405)
