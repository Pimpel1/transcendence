import io
import gzip
import json
import urllib.parse
import urllib.request

from django.conf import settings


def exchange_code_for_token(code):
    if not code:
        raise ValueError('Authorization code missing')
    token_url = 'https://api.intra.42.fr/oauth/token'
    params = {
        'grant_type': 'authorization_code',
        'client_id': settings.PONG_OAUTH_UID,
        'client_secret': settings.PONG_OAUTH_42_SECRET,
        'code': code,
        'redirect_uri':
            f"https://{settings.IP_ADDRESS}:8443/auth-service/oauth-callback"
    }

    data = urllib.parse.urlencode(params).encode('utf-8')
    headers = {
        'User-Agent': 'Pong',
        'Accept-Encoding': 'gzip',
        'Connection': 'keep-alive'
    }
    req = urllib.request.Request(
        token_url,
        data=data,
        headers=headers,
        method='POST'
        )

    try:
        with urllib.request.urlopen(req) as response:
            response_data = unzip_response(response)
            if 'access_token' not in response_data:
                raise Exception('Failed to fetch access token')
            return response_data['access_token']
    except urllib.error.HTTPError as e:
        error_message = e.read().decode()
        raise Exception(f'HTTP Error: {e.code} - {error_message}')
    except Exception as e:
        raise Exception(f'Unexpected Error: {str(e)}')


def get_user_data(access_token):
    user_info_url = 'https://api.intra.42.fr/v2/me'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': 'Pong',
        'Accept-Encoding': 'gzip',
        'Connection': 'close'
    }

    req = urllib.request.Request(user_info_url, headers=headers, method='GET')

    try:
        with urllib.request.urlopen(req) as response:
            return unzip_response(response)
    except urllib.error.HTTPError as e:
        error_message = e.read().decode()
        raise Exception(f'HTTP Error: {e.code} - {error_message}')
    except Exception as e:
        raise Exception(f'Unexpected Error: {str(e)}')


def unzip_response(response):
    buf = io.BytesIO(response.read())
    if buf.getbuffer().nbytes == 0:
        raise ValueError('Empty response body')
    with gzip.GzipFile(fileobj=buf) as f:
        return json.loads(f.read().decode('utf-8'))
