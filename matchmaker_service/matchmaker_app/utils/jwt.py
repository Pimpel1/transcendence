import http.client
import json
import logging
import ssl

from django.conf import settings
from django.http import JsonResponse
from http.client import HTTPSConnection


logger = logging.getLogger('matchmaker-service')


def _get_auth_service_csrf_token():
    context = ssl._create_unverified_context()
    conn = http.client.HTTPSConnection('auth-service', 8001, context=context)

    try:
        conn.request('GET', '/get-csrf-token/')
        csrf_response = conn.getresponse()
        cookies = csrf_response.getheader('Set-Cookie')
        if not cookies:
            raise ValueError('No Set-Cookie header in response')

        for cookie in cookies.split(','):
            if 'csrf_token_auth_service=' in cookie:
                return cookie.split(
                    'csrf_token_auth_service='
                )[1].split(';')[0]

        raise ValueError('CSRF token not found in response cookies')
    finally:
        conn.close()


def _validate_auth_service_jwt(jwt, csrf_token):
    context = ssl._create_unverified_context()
    conn = HTTPSConnection('auth-service', 8001, context=context)

    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token,
        'Cookie': f'csrf_token_auth_service={csrf_token}; jwt={jwt}',
        'Referer': f"https://{settings.IP_ADDRESS}:8003",
    }

    try:
        conn.request('POST', '/api/validate-jwt/', headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(
                f'Error validating JWT token. Status code: {response.status}'
            )
        response_data = response.read().decode('utf-8')
        return json.loads(response_data)
    finally:
        conn.close()


def validate(request):
    try:
        jwt = request.COOKIES.get('jwt')
        if not jwt:
            raise ValueError('No JWT token in request cookies')

        csrf_token = _get_auth_service_csrf_token()
        response_data = _validate_auth_service_jwt(
            jwt, csrf_token
        )

        request.jwt_username = response_data.get('username')
        request.jwt_email = response_data.get('email')
        request.jwt_displayname = response_data.get('displayname')

        logger.debug(
            f'JWT is valid '
            f'(user: {request.jwt_username}, '
            f'email: {request.jwt_email}, '
            f'displayname: {request.jwt_displayname})'
        )

        return JsonResponse({'message': 'Authorized'}, status=200)

    except Exception as e:
        logger.error(f'JWT validation failed [{e}]')
        return JsonResponse(
            {'message': 'Unauthorized', 'error': str(e)}, status=401
        )


def get_username(jwt):
    csrf_token = _get_auth_service_csrf_token()
    try:
        response_data = _validate_auth_service_jwt(jwt, csrf_token)
        return response_data.get('username')
    except Exception as e:
        if 'Unauthorized' in str(e):
            return None
        raise e
