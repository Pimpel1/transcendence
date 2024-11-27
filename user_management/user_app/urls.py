from django.urls import path

from . import views


# API Endpoints
# -------------
# GET  /get-csrf-token/                : Get CSRF token
# POST /login/                          : Logs in user
#                                       {
#                                           "oauth_token": str,  # Required
#                                       }
# PUT /update/                         : Updates user details
#                                       {
#                                           "display_name": str,  # Optional
#                                           "language": str,  # Optional
#                                           "avatar": image,  # Optional
#                                       }
# GET /user-details/                   : Get user details
# GET /my-friends/                     : Get user's friends
# POST /send-friend-request/           : Send friend request
#                                       {
#                                           "username": str  # Required
#                                       }
# DELETE /delete-friend/               : Delete friend
#                                       {
#                                           "username": str  # Required
#                                       }
# GET /all-users/                      : Get all users
# GET /get-displaynames/               : Get display names of users
#                                       {
#                                           "usernames": list  # Required
#                                       }
# GET /health/                         : Health check


urlpatterns = [
    path(
        'get-csrf-token/',
        views.getCsrfToken,
        name='get-csrf-token'
    ),
    path(
        'login/',
        views.UserView.as_view(),
        name='login'
    ),
    path(
        'update/',
        views.UserView.as_view(),
        name='update'
    ),
    path(
        'user-details/',
        views.UserView.as_view(),
        name='user-details'
    ),
    path(
        'my-friends/',
        views.FriendView.as_view(),
        name='my-friends'
    ),
    path(
        'send-friend-request/',
        views.FriendView.as_view(),
        name='send-friend-request'
    ),
    path(
        'delete-friend/',
        views.FriendView.as_view(),
        name='delete-friend'
    ),
    path(
        'all-users/',
        views.get_all_users,
        name='all-users'
    ),
    path(
        'get-displaynames/',
        views.get_displaynames_from_usernames,
        name='get-displaynames'
    ),
    path(
        'health/',
        views.HealthCheck,
        name='health-check'
    )
]
