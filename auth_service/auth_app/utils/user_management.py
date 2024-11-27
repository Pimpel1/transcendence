import json
import logging
import ssl

from django.conf import settings
from http.client import HTTPSConnection


logger = logging.getLogger('user-management')


def user_management_login(email, oauth_token):
    response_data = None

    try:
        context = ssl._create_unverified_context()
        conn = HTTPSConnection('user-management', 8003, context=context)

        conn.request('GET', '/get-csrf-token/')
        csrf_response = conn.getresponse()
        cookies = csrf_response.getheader('Set-Cookie')

        if not cookies:
            raise ValueError('No Set-Cookie header in response')

        # Extract CSRF token from cookies
        csrf_token = None
        for cookie in cookies.split(','):
            if 'csrf_token_user_management=' in cookie:
                csrf_token = cookie.\
                    split('csrf_token_user_management=')[1].split(';')[0]
                break

        if not csrf_token:
            raise ValueError('CSRF token not found in response cookies')

        # Make authenticated POST request with CSRF token
        conn = HTTPSConnection('user-management', 8003, context=context)
        payload = json.dumps({'email': email, 'oauth_token': oauth_token})
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
            'Cookie': cookies,  # Pass all cookies to maintain session
            'Referer': f"https://{settings.IP_ADDRESS}:8001/login/",
        }

        conn.request('POST', '/login/', body=payload, headers=headers)
        response = conn.getresponse()

        if response.status in [200, 201]:
            response_data = response.read().decode('utf-8')
        else:
            raise ValueError(f'{response.status} {response.reason}')

    except Exception as e:
        logger.error(
            f'Failed to login user (email: {email}) with user-management '
            f'[{e}]'
        )

    finally:
        conn.close()

    return response_data
