import json
import logging
import requests
import base64

from base64 import b64encode

from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import (
    csrf_exempt,
    ensure_csrf_cookie,
    csrf_protect
)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.core.files.base import ContentFile
from django.views import View

from .models import UserProfile
from .services import (
    get_data_from_42,
    get_avatar_bytes,
    create_user_in_matchmaker,
    get_wins_losses_status,
    get_friends_list,
    get_non_friends_list,
    get_friend_requests_list,
    get_displayname_from_username,
    increment_suffix,
    get_user_info,
    get_users_i_sent_request_to
)


logger = logging.getLogger('user-management')


User = get_user_model()


@ensure_csrf_cookie
def getCsrfToken(request):
    csrf_token = request.META.get('CSRF_COOKIE', '')
    return JsonResponse({'csrfToken': csrf_token})


class UserView(View):
    def get(self, request):
        logger.debug(f'GET /user-details/ [{request.META.get("REMOTE_ADDR")}]')
        try:
            jwt = request.COOKIES.get('jwt')
            if not jwt:
                raise Exception('JWT token is missing')
            user_info = get_user_info(jwt)
            email = user_info.get('email')
            logger.debug(f"Extracted email: {email}")
            user = get_object_or_404(User, email=email)
            stats = get_wins_losses_status(user.username)
            with open(user.userprofile.avatar.path, "rb") as avatar_file:
                avatar_base64 = b64encode(avatar_file.read()).decode('utf-8')
            return JsonResponse({
                'email': user.email,
                'username': user.username,
                'displayname': user.displayname,
                'avatar': avatar_base64,
                'language': user.userprofile.language,
                'wins': stats.get('wins', -1),
                'losses': stats.get('losses', -1),
                'status': stats.get('status', False),
                'sent_request_to': get_users_i_sent_request_to(jwt),
                'friends': get_friends_list(jwt)
            })
        except Exception as e:
            logger.error(f'GET /user-details/ [{e}]')
            return JsonResponse(
                {'error': f'Failed to get user info: {e}'}, status=401
            )

    @method_decorator(csrf_protect)
    def post(self, request):
        User = get_user_model()

        logger.debug(
            f'POST /login/ [{request.META.get("REMOTE_ADDR")}]'
            f'[{request.body.decode("utf-8")}]'
        )
        try:
            data = json.loads(request.body)
            oauth_token = data.get('oauth_token')

            if not oauth_token:
                logger.error('POST /login/ \
                             [Missing oauth_token in request data]')
                return JsonResponse(
                    {'error': 'oauth_token is required'},
                    status=400
                    )

            response = get_data_from_42(oauth_token)

            if response['status_code'] == 200:

                email = response['email']
                user, created = User.objects.get_or_create(email=email)

                if created:
                    unique_displayname = response['displayname']
                    user_exists = User.objects.filter(
                        displayname=unique_displayname).exists()
                    while user_exists:
                        unique_displayname = increment_suffix(
                            unique_displayname)
                        user_exists = User.objects.filter(
                            displayname=unique_displayname).exists()

                    user.username = response['username']
                    user.displayname = unique_displayname
                    user.save()

                    user_profile = UserProfile.objects.create(user=user)

                    if response['avatar_url']:
                        get_avatar_bytes(response['avatar_url'], user_profile)
                    else:
                        return JsonResponse(
                            {'error': 'No avatar URL provided by 42 API'},
                            status=400
                            )

                    matchmaker_status_code = create_user_in_matchmaker(
                        user.username
                        )
                    if matchmaker_status_code not in [201, 400]:
                        user.delete()
                        return JsonResponse(
                            {'error': 'Failed to register user \
                             with matchmaker-service'},
                            status=500
                            )

                avatar_bytes = (
                    user.userprofile.avatar.read()
                    if user.userprofile.avatar
                    and user.userprofile.avatar != "avatars/default.png"
                    else None
                )

                if avatar_bytes is None:
                    avatar_bytes = get_avatar_bytes(
                        response['avatar_url'],
                        user.userprofile
                        )
                user_information = {
                    'email': user.email,
                    'username': user.username,
                    'avatar': (
                                b64encode(avatar_bytes).decode('utf-8')
                                if avatar_bytes
                                else None
                            ),
                    'display_name': user.displayname,
                }

                return JsonResponse(user_information, status=200)

            else:
                error_message = "Failed to retrieve user data: " + \
                                {response['status_code']}
                logger.error(f'POST /login/ [{error_message}]')
                return JsonResponse(
                    {'error': error_message},
                    status=response['status_code']
                    )

        except json.JSONDecodeError as e:
            logger.error(f'POST /login/ [Invalid JSON received; {e}]')
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        except requests.RequestException as e:
            logger.error(f'POST /login/ [External request failed; {e}]')
            return JsonResponse(
                {'error': 'External request failed'},
                status=502
                )

        except Exception as e:
            logger.error(f'POST /login/ [Internal server error; {e}]')
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

    @method_decorator(csrf_protect)
    def put(self, request):
        logger.debug(
            f'PUT /update-profile/ [{request.META.get("REMOTE_ADDR")}]'
            f'[{request.body.decode("utf-8")}]'
        )
        try:
            data = json.loads(request.body)
            logger.debug(f"UpdateProfile Request body: {data}")
            token = request.COOKIES.get('jwt')
            if not token:
                logger.error('PUT /update-profile/ \
                             [Missing jwt_token in request data]')
                return JsonResponse({'error': 'Token is missing'}, status=400)

            user_info = get_user_info(token)
            email = user_info.get('email')
            if not email:
                logger.error('PUT /update-profile/ [Invalid token]')
                return JsonResponse({'error': 'Invalid token'}, status=401)

            user = get_object_or_404(User, email=email)

            displayname = data.get('displayname')
            avatar_base64 = data.get('avatar')
            language = data.get('language')

            if language:
                logger.debug(f"Language: {language}")
                if language == "english":
                    user.userprofile.language = 'en'
                elif language == "dutch":
                    user.userprofile.language = 'nl'
                else:
                    user.userprofile.language = 'fr'

            if displayname:
                if check_displayname_exists(displayname) and\
                      user.displayname != displayname:
                    logger.error('PUT /update-profile/ \
                                 [Display name must be unique]')
                    return JsonResponse(
                        {'error': 'Display name must be unique'},
                        status=401
                        )
                user.displayname = displayname

            if avatar_base64:
                try:
                    format, imgstr = avatar_base64.split(';base64,')
                    ext = format.split('/')[-1]
                    avatar_data = base64.b64decode(imgstr)
                    avatar_filename = f"{user.username}_avatar.{ext}"

                    user.userprofile.avatar.save(
                        avatar_filename,
                        ContentFile(avatar_data),
                        save=True
                        )
                except (ValueError, IndexError) as e:
                    logger.error(f"Base64 decoding error: {e}")
                    return JsonResponse(
                        {'error': 'Invalid image format'},
                        status=400
                        )

            user.userprofile.save()
            user.save()

            return JsonResponse(
                {'success': 'Profile updated successfully'},
                status=200
                )

        except json.JSONDecodeError:
            logger.error('PUT /update-profile/ [Invalid JSON format]')
            return JsonResponse(
                {'error': 'An internal server error occurred'},
                status=500
                )


def check_displayname_exists(displayname):
    return User.objects.filter(displayname=displayname).exists()


@csrf_exempt
def HealthCheck(request):
    return JsonResponse({'status': 'ok'})


class FriendView(View):

    def get(self, request):
        try:
            jwt = request.COOKIES.get('jwt')
            friends_list = get_friends_list(jwt)

            return JsonResponse({'friends': friends_list})
        except Exception as e:
            logger.error(f"Error fetching friends: {str(e)}")
            return JsonResponse({'error': 'An error occurred.'}, status=500)

    @method_decorator(csrf_protect)
    def post(self, request):
        try:

            logger.info(f"POST /send-friend-request/ \
                        [{request.META.get('REMOTE_ADDR')}]")
            body = json.loads(request.body)
            username = body.get('username')

            if not username:
                return JsonResponse(
                    {'error': 'Username is required'},
                    status=400
                    )

            jwt = request.COOKIES.get('jwt')
            user_info = get_user_info(jwt)
            email = user_info.get('email')

            user = get_object_or_404(User, email=email)
            user_profile = UserProfile.objects.get(user=user)

            friend_user = get_object_or_404(User, username=username)
            friend_profile = UserProfile.objects.get(user=friend_user)

            if user_profile in friend_profile.wannabe_friends.all():
                user_profile.friends.add(friend_profile)
                friend_profile.friends.add(user_profile)

                user_profile.wannabe_friends.remove(friend_profile)
                friend_profile.wannabe_friends.remove(user_profile)

                return JsonResponse({'success': f'new friend: \
                                     {friend_user.username}'})

            if friend_profile in user_profile.wannabe_friends.all():
                return JsonResponse(
                    {'error': 'Friend request already sent'},
                    status=400
                    )

            user_profile.wannabe_friends.add(friend_profile)
            return JsonResponse({'success': 'Friend request sent'})

        except Exception as e:
            logger.error(f"Error sending friend request: {str(e)}")
            return JsonResponse({'error': 'An error occurred.'}, status=500)

    @method_decorator(csrf_protect)
    def delete(self, request):
        try:

            jwt = request.COOKIES.get('jwt')
            if not jwt:
                return JsonResponse(
                    {'error': 'JWT token is missing'},
                    status=400
                    )

            user_info = get_user_info(jwt)
            if not user_info:
                return JsonResponse({'error': 'Invalid JWT token'}, status=400)

            email = user_info.get('email')

            user = get_object_or_404(User, email=email)
            user_profile = UserProfile.objects.get(user=user)

            body = json.loads(request.body)
            friend_username = body.get('username')

            if not friend_username:
                return JsonResponse(
                    {'error': 'Username is required'},
                    status=400
                    )

            friend_user = get_object_or_404(User, username=friend_username)
            friend_profile = UserProfile.objects.get(user=friend_user)

            if friend_profile in user_profile.friends.all():
                user_profile.friends.remove(friend_profile)
                friend_profile.friends.remove(user_profile)
                return JsonResponse(
                    {'success': f'{friend_user.username} has been unfriended'}
                    )
            else:
                return JsonResponse(
                    {'error': f'{friend_user.username} is not a friend'},
                    status=400)

        except Exception as e:
            logger.error(f"Error deleting friend: {str(e)}")
            return JsonResponse({'error': 'An error occurred.'}, status=500)


def get_all_users(request):
    try:
        if request.method != 'GET':
            return JsonResponse(
                {'error': 'Invalid request method'},
                status=405
                )

        jwt = request.COOKIES.get('jwt')
        if not jwt:
            return JsonResponse({'error': 'JWT token is missing'}, status=400)

        user_info = get_user_info(jwt)
        if not user_info:
            return JsonResponse({'error': 'Invalid JWT token'}, status=400)

        return JsonResponse({
            'users': get_non_friends_list(jwt),
            'friend_requests': get_friend_requests_list(jwt),
            'friends': get_friends_list(jwt)
        })

    except Exception as e:
        logger.error(f"Error fetching non-friends and requests: {str(e)}")
        return JsonResponse({'error': 'An error occurred.'}, status=500)


@csrf_protect
def get_displaynames_from_usernames(request):
    try:
        if request.method != 'POST':
            return JsonResponse(
                {'error': 'Invalid request method'},
                status=405
                )

        usernames = json.loads(request.body)

        if not usernames:
            return JsonResponse(
                {'error': 'Usernames are required'},
                status=400
                )

        displaynames = []
        for username in usernames:
            displayname = get_displayname_from_username(username)
            if displayname:
                displaynames.append(displayname)

        return JsonResponse({'displaynames': displaynames})

    except Exception as e:
        logger.error(f"Error getting displaynames from usernames: {str(e)}")
        return JsonResponse({'error': 'An error occurred.'}, status=500)
