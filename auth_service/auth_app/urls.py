from django.urls import path

from . import views


# API Endpoints
# -------------
# GET  /api/oauth-login/               : Redirects to 42 OAuth login page
#
# GET  /oauth-callback/            : Exchanges code for OAuth token
#                                           + sends OTP
#
# POST /api/verify-otp/                    : Verifies OTP and returns JWT
#                                       {
#                                           "otp": str  # Required
#                                       }
#
# POST /api/validate-jwt/                  : Validates JWT
#                                       {
#                                           "jwt": str  # Required
#                                       }
#
# GET  /health/                        : Health check
#
# GET  /get-csrf-token/                : Get CSRF token
#
# POST /api/logout/                     : Logs out user


urlpatterns = [
    path(
        'api/oauth-login/',
        views.OAuthLoginView.as_view(),
        name='oauth-login'
    ),
    path(
        'oauth-callback/',
        views.OAuthCallbackView.as_view(),
        name='oauth-callback'
    ),
    path(
        'api/verify-otp/',
        views.VerifyOtpView.as_view(),
        name='verify-otp'
    ),
    path(
        'api/validate-jwt/',
        views.ValidateJwtView.as_view(),
        name='validate-jwt'
    ),
    path(
        'health/',
        views.HealthCheck.as_view(),
        name='health'
    ),
    path(
        'get-csrf-token/',
        views.getCsrfToken.as_view(),
        name='get-csrf-token'
    ),
    path(
        'api/logout/',
        views.Logout.as_view(),
        name='logout'
    )
]
