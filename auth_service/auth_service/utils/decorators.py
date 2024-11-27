import logging
from functools import wraps

from django.http import JsonResponse


logger = logging.getLogger('auth-service')


def handle_exceptions(function):
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        try:
            return function(request, *args, **kwargs)

        except Exception as e:
            logger.error(f'{request.method} {request.path} - Error: {str(e)}')
            return JsonResponse(
                {'error': 'An internal server error occurred'},
                status=500
            )

    return wrapper


def log_request(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        method = request.method
        path = request.path
        query_string = request.META.get('QUERY_STRING')
        remote_ip = request.META.get('REMOTE_ADDR', 'unknown')
        remote_port = request.META.get('REMOTE_PORT', 'unknown')

        try:
            if request.body:
                decoded_body = request.body.decode('utf-8')
                body = (
                    decoded_body[:20] + '...'
                    if len(decoded_body) > 20
                    else decoded_body
                )
            else:
                body = ''
        except UnicodeDecodeError:
            body = '*Non-decodable body*'

        logger.debug(
            f'{method} {path} [{query_string}] [{body}] '
            f'[{remote_ip}:{remote_port}]'
        )

        return view_func(request, *args, **kwargs)

    return wrapper
