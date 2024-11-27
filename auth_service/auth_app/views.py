import json
import logging

from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect

from auth_app.utils.jwt import jwt_decode, make_jwt
from auth_app.utils.oauth import exchange_code_for_token, get_user_data
from auth_app.utils.two_factor_auth import get_otp, email_otp
from auth_app.utils.user_management import user_management_login
from auth_service.utils.decorators import log_request, handle_exceptions
from auth_service.utils.mixins import MethodNotAllowedMixin


logger = logging.getLogger('auth-service')


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class OAuthLoginView(MethodNotAllowedMixin, View):
    # GET /api/oauth-login/ : Redirects to 42 OAuth login page

    def get(self, request):
        request.session.create()
        oauthUrl = (
            'https://api.intra.42.fr/oauth/authorize?'
            f'client_id={settings.PONG_OAUTH_UID}&'
            f'redirect_uri=https%3A%2F%2F{settings.IP_ADDRESS}%3A8443%2F'
            'auth-service%2F'
            'oauth-callback&'
            'response_type=code&scope=public&'
        )

        return HttpResponseRedirect(oauthUrl)


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class OAuthCallbackView(MethodNotAllowedMixin, View):
    # Exchanges code for OAuth token and sends OTP

    def get(self, request):
        code = request.GET.get('code')
        oauth_token = exchange_code_for_token(code)
        user_data = get_user_data(oauth_token)
        email = user_data.get('email')
        username = user_data.get('login')
        displayname = user_data.get('displayname')
        otp = get_otp()
        email_otp(email, otp)
        request.session['email'] = email
        request.session['oauth_token'] = oauth_token
        request.session['otp'] = otp
        request.session.save()

        return HttpResponseRedirect(
            f'/two-factor-auth?'
            f'email={email}&'
            f'username={username}&'
            f'displayname={displayname}'
            )


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class VerifyOtpView(MethodNotAllowedMixin, View):
    # POST /api/verify-otp/ : Verifies OTP and sets JWT cookie
    #                   {otp: string}

    @method_decorator(csrf_protect)
    def post(self, request):
        try:
            data = json.loads(request.body)
            otp = data.get('otp')
            if not otp:
                raise ValueError('OTP is required')

            session_otp = request.session.get('otp')
            if otp == session_otp:
                email = request.session.get('email')
                oauth_token = request.session.get('oauth_token')
                raw_user_info = user_management_login(email, oauth_token)
                if raw_user_info is None:
                    raise Exception(
                        'No login response received from User-management'
                    )
                jwt = make_jwt(settings.JWT_SECRET_KEY, raw_user_info)
                response = JsonResponse({'success': True})
                response.set_cookie(
                    key='jwt',
                    value=jwt,
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                    max_age=3600,
                )
                return response

            else:
                logger.error(
                    'POST /api/verify-otp/ [Invalid OTP]'
                )
                return JsonResponse(
                    {'error': 'Invalid OTP'}, status=403
                )

        except json.JSONDecodeError:
            logger.error('POST /api/verify-otp/ [Invalid JSON]')
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        except ValueError as ve:
            logger.error(f'POST /api/verify-otp/ [{ve}]')
            return JsonResponse({'error': str(ve)}, status=400)


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class ValidateJwtView(MethodNotAllowedMixin, View):
    # POST /api/validate-jwt/ : Validates JWT and returns email
    #                      {jwt: string}

    @method_decorator(csrf_protect)
    def post(self, request):
        try:
            jwt = request.COOKIES.get('jwt') \
                or request.body and json.loads(request.body).get('jwt')
            if not jwt:
                raise ValueError('jwt is required')

            secret_key = settings.JWT_SECRET_KEY
            payload = jwt_decode(jwt, secret_key)
            email = payload.get('email')
            username = payload.get('username')
            displayname = payload.get('displayname')
            return JsonResponse(
                {
                    'email': email,
                    'username': username,
                    'displayname': displayname
                }
            )

        except json.JSONDecodeError:
            logger.error('POST /api/validate-jwt/ [Invalid JSON]')
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        except ValueError as ve:
            logger.warning(f'POST /api/validate-jwt/ [{ve}]')
            return JsonResponse({'error': str(ve)}, status=401)


@method_decorator(handle_exceptions, name='dispatch')
class HealthCheck(MethodNotAllowedMixin, View):
    # GET /health/ : Returns status ok

    def get(self, request):
        return JsonResponse({'status': 'ok'})


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class getCsrfToken(MethodNotAllowedMixin, View):
    # GET /get-csrf-token/ : Returns CSRF token

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        csrf_token = request.META.get('CSRF_COOKIE', '')
        return JsonResponse({'csrfToken': csrf_token})


@method_decorator(log_request, name='dispatch')
@method_decorator(handle_exceptions, name='dispatch')
class Logout(MethodNotAllowedMixin, View):
    # POST /logout/ : Logs out user by deleting JWT cookie

    @method_decorator(csrf_protect)
    def post(self, request):
        response = JsonResponse({'success': True})
        response.delete_cookie('jwt')
        return response
