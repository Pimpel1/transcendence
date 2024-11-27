import json
import logging
import os
import re
import ssl
import http.client
from base64 import b64encode
from http.client import HTTPSConnection
import requests
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404

from .models import UserProfile


logger = logging.getLogger('user-management')


User = get_user_model()


def get_wins_losses_status(username):
    try:
        context = ssl._create_unverified_context()

        conn = http.client.HTTPSConnection(
            'matchmaker-service',
            8002,
            context=context
            )

        endpoint = f'/api/players/{username}/'

        conn.request('GET', endpoint)

        response = conn.getresponse()

        data = response.read()

        if response.status == 200:

            logger.debug(f"get_wins_losses_status: {data}")
            data_str = data.decode('utf-8')
            data_json = json.loads(data_str)

            return {
                'wins': data_json.get('total_wins', -1),
                'losses': data_json.get('total_losses', -1),
                'status': data_json.get('connected', False)
            }
        else:
            logger.error(
                "Error fetching stats for in get_wins_losses_status " +
                {response.status})
            return None

    except Exception as e:
        logger.error(f"Error during HTTP request: {str(e)}")
        return None

    finally:
        conn.close()


def increment_suffix(base_str):
    match = re.match(r'(\D*)(\d*)$', base_str)

    if match:
        base_part = match.group(1)
        suffix_part = match.group(2)

        if suffix_part:
            new_suffix = str(int(suffix_part) + 1)
        else:
            new_suffix = '1'

        new_str = base_part + new_suffix
        return new_str
    else:
        return base_str + '1'


def get_user_info(token):

    try:
        context = ssl._create_unverified_context()
        conn = http.client.HTTPSConnection(
            'auth-service', 8001, context=context)

        conn.request('GET', '/get-csrf-token/')
        csrf_response = conn.getresponse()
        cookies = csrf_response.getheader('Set-Cookie')

        if not cookies:
            raise ValueError('No Set-Cookie header in response')

        csrf_token = None
        for cookie in cookies.split(','):
            if 'csrf_token_auth_service=' in cookie:
                csrf_token = cookie.split(
                    'csrf_token_auth_service=')[1].split(';')[0]
                break

        if not csrf_token:
            raise ValueError('CSRF token not found in response cookies')

        conn = HTTPSConnection('auth-service', 8001, context=context)
        payload = json.dumps({'jwt': token})
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
            'Cookie': cookies,
            'Referer': f"https://{settings.IP_ADDRESS}:8003",
                  }
        response_data = None

        conn.request('POST', '/api/validate-jwt/',
                     body=payload, headers=headers)
        response = conn.getresponse()

        if response.status == 200:
            response_data = response.read().decode('utf-8')
            response_data = json.loads(response_data)
        else:
            logger.error(f'Failed to send message from get_user_info \
                  function inside updateProfile view \
                  to auth-service: {response.status} {response.reason}')
            response_data = None
    except Exception as e:
        logger.error(f'Failed to send message from get_user_info \
              function inside updateProfile view to auth-service: {e}')
        response_data = None
    finally:
        conn.close()

    return response_data


def create_user_in_matchmaker(username):
    try:
        context = ssl._create_unverified_context()

        conn = http.client.HTTPSConnection(
            'matchmaker-service',
            8002,
            context=context
        )

        conn.request('GET', '/get-csrf-token/')
        csrf_response = conn.getresponse()
        cookies = csrf_response.getheader('Set-Cookie')

        if not cookies:
            raise ValueError(
                'No Set-Cookie header found in CSRF token response'
                )

        csrf_token = None
        for cookie in cookies.split(','):
            if 'csrf_token_matchmaker_service=' in cookie:
                csrf_token = cookie.split(
                    'csrf_token_matchmaker_service=')[1].split(
                        ';')[0]
                break

        if not csrf_token:
            raise ValueError('CSRF token not found in cookies')

        payload = json.dumps({'name': username})
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
            'X-API-Key': settings.MATCHMAKER_SERVICE_API_KEY,
            'Cookie': cookies,
            'Referer': f"https://{settings.IP_ADDRESS}:8003",
        }

        conn = http.client.HTTPSConnection(
            'matchmaker-service',
            8002,
            context=context)
        conn.request('POST', '/api/players/', body=payload, headers=headers)
        response = conn.getresponse()

        if response.status != 201:
            raise ValueError(f'{response.status} {response.reason}')

    except Exception as e:
        logger.error(
            f'Failed to register user \'{username}\' with matchmaker-service '
            f'[{e}]'
        )

    finally:
        conn.close()
        return response.status


def get_friends_list(jwt):
    try:
        user_info = get_user_info(jwt)
        email = user_info.get('email')

        user = get_object_or_404(User, email=email)
        user_profile = UserProfile.objects.get(user=user)

        friends = user_profile.friends.all()

        friends_list = []
        for friend in friends:
            friend_profile = friend
            if friend_profile.avatar:
                with open(friend_profile.avatar.path, "rb") as avatar_file:
                    avatar_base64 = b64encode(
                        avatar_file.read()).decode('utf-8')
            else:
                avatar_base64 = None
            stats = get_wins_losses_status(friend.user.username)

            friends_list.append({
                'username': friend.user.username,
                'displayname': friend.user.displayname,
                'avatar': avatar_base64,
                'wins': stats.get('wins', -1),
                'losses': stats.get('losses', -1),
                'status': stats.get('connected', 'False')
            })

        return friends_list

    except Exception as e:
        logger.error(f"Error fetching friends: {str(e)}")
        return []


def get_friend_requests_list(jwt):
    try:
        user_info = get_user_info(jwt)
        email = user_info.get('email')

        user = get_object_or_404(User, email=email)

        user_profile = UserProfile.objects.get(user=user)

        friend_requests = user_profile.wannabe_requests.all()

        friend_requests_list = []
        for friend in friend_requests:
            if friend.avatar:
                with open(friend.avatar.path, "rb") as avatar_file:
                    avatar_base64 = b64encode(
                        avatar_file.read()).decode('utf-8')
            else:
                avatar_base64 = None

            stats = get_wins_losses_status(friend.user.username)
            friend_requests_list.append({
                'username': friend.user.username,
                'displayname': friend.user.displayname,
                'avatar': avatar_base64,
                'wins': stats.get('wins', -1),
                'losses': stats.get('losses', -1),
                'status': stats.get('connected', 'False')
            })

        return friend_requests_list

    except Exception as e:
        logger.error(f"Error fetching friend requests: {str(e)}")
        return []


def get_non_friends_list(jwt):
    try:
        user_info = get_user_info(jwt)
        email = user_info.get('email')

        user = get_object_or_404(User, email=email)

        user_profile = UserProfile.objects.get(user=user)

        friends = user_profile.friends.all()

        wannabe_friends = user_profile.wannabe_requests.all()

        other_users = UserProfile.objects.exclude(
            user=user
        ).exclude(
            id__in=friends
        ).exclude(
            id__in=wannabe_friends
        )

        other_users_list = []
        for other_user in other_users:
            if other_user.avatar:
                with open(other_user.avatar.path, "rb") as avatar_file:
                    avatar_base64 = b64encode(
                        avatar_file.read()).decode(
                            'utf-8')
            else:
                avatar_base64 = None

            stats = get_wins_losses_status(other_user.user.username)

            other_users_list.append({
                'username': other_user.user.username,
                'displayname': other_user.user.displayname,
                'avatar': avatar_base64,
                'wins': stats.get('wins', -1),
                'losses': stats.get('losses', -1),
                'status': stats.get('connected', 'False')
            })

        return other_users_list

    except Exception as e:
        logger.error(f"Error fetching non-friends: {str(e)}")
        return []


def get_data_from_42(access_token):
    try:
        url = "https://api.intra.42.fr/v2/me"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            # create list of information to return
            return {
                'username': data['login'],
                'displayname': data['displayname'],
                'email': data['email'],
                'avatar_url': data.get(
                    'image', {}).get(
                        'versions', {}).get(
                            'small'),
                'status_code': 200
            }
        else:
            logger.error(
                "Error fetching data from 42: " +
                {response.status_code})
            return {
                'status_code': response.status_code
            }
    except Exception as e:
        logger.error(f"Error fetching data from 42: {str(e)}")
        return {
            'status_code': 500
        }


def get_avatar_bytes(avatar_url, user_profile):
    avatar_response = requests.get(avatar_url)
    if avatar_response.status_code == 200:
        file_name = os.path.basename(urlparse(avatar_url).path)
        user_profile.avatar.save(
            file_name,
            ContentFile(avatar_response.content),
            save=True)
        return avatar_response.content
    else:
        return None

# Profile related functions


def get_displayname_from_username(username):
    try:
        user = User.objects.get(username=username)
        return user.displayname
    except ObjectDoesNotExist:
        return username


def get_users_i_sent_request_to(jwt):
    try:
        user_info = get_user_info(jwt)
        if not user_info or 'email' not in user_info:
            logger.error('Invalid JWT or missing email in token.')
            return []

        email = user_info.get('email')

        user = get_object_or_404(User, email=email)
        user_profile = UserProfile.objects.get(user=user)

        users_sent_friend_requests_to = user_profile.wannabe_friends.all()

        result = [
            profile.user.username
            for profile in users_sent_friend_requests_to
        ]

        logger.debug(f"Users sent friend requests: {result}")
        return result

    except User.DoesNotExist:
        logger.error('User not found.')
        return []

    except UserProfile.DoesNotExist:
        logger.error('User profile not found.')
        return []

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return []
