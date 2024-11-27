import json
import logging
import time
import base64
import hashlib
import hmac


logger = logging.getLogger('auth-service')


def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def base64url_decode(data):
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def jwt_encode(payload, secret_key):
    """Encode a JWT token."""
    header = {
        'alg': 'HS256',
        'typ': 'JWT'
    }
    encoded_header = base64url_encode(
        json.dumps(header).encode('utf-8'))
    encoded_payload = base64url_encode(
        json.dumps(payload).encode('utf-8'))

    signature = hmac.new(
        secret_key.encode('utf-8'),
        f'{encoded_header}.{encoded_payload}'.encode('utf-8'),
        hashlib.sha256
    ).digest()
    encoded_signature = base64url_encode(signature)

    token = f'{encoded_header}.{encoded_payload}.{encoded_signature}'
    return token


def jwt_decode(token, secret_key):
    try:
        encoded_header, encoded_payload, received_signature = token.split('.')
        payload = json.loads(base64url_decode(encoded_payload))

        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            f'{encoded_header}.{encoded_payload}'.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_encoded_signature = base64url_encode(expected_signature)

        if received_signature != expected_encoded_signature:
            raise ValueError('Invalid token signature')

        if payload.get('exp') and payload['exp'] < time.time():
            raise ValueError('Token has expired')

        return payload

    except (ValueError, KeyError, json.JSONDecodeError) as e:
        raise ValueError(f'Invalid token: {str(e)}')


def make_jwt(secret_key, raw_user_information, exp=3600):
    user_information = json.loads(raw_user_information)

    username = user_information.get('username')
    displayname = user_information.get('displayname')
    email = user_information.get('email')

    payload = {
        'username': username,
        'displayname': displayname,
        'email': email,
        'exp': int(time.time()) + exp
    }

    logger.debug(
        f'Creating JWT token for user \'{username}\' '
        f'(display name: \'{displayname}\', '
        f'email: \'{email}\')'
    )

    return jwt_encode(payload, secret_key)
