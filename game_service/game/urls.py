from django.urls import path

from . import views


# API Endpoints
# -------------
# PUT   /api/game/<str:game_id>/    : Create a game
#
# GET   /api/game/<str:game_id>/    : Get a game's current state
#
# PUT   /api/start/<str:game_id>/   : Start a game
#
# PUT   /api/join/<str:game_id>/    : Add a player to a game
#                                   {
#                                       "side": str,    # Required
#                                   }
#
# PUT   /api/control/<str:game_id>/ : Send control message
#                                   {
#                                       "side": str,    # Required
#                                       "key": str      # Required
#                                       "event": str,   # Required
#                                   }
#
# GET   /get-csrf-token/            : Get CSRF token
#
# GET   /health/                    : Health check

urlpatterns = [
    path(
        'api/game/<str:game_id>/',
        views.Game.as_view(),
        name='game'
    ),
    path(
        'api/start/<str:game_id>/',
        views.Start.as_view(),
        name='start'
    ),
    path(
        'api/join/<str:game_id>/',
        views.Join.as_view(),
        name='join'
    ),
    path(
        'api/control/<str:game_id>/',
        views.Control.as_view(),
        name='control'
    ),
    path(
        'get-csrf-token/',
        views.getCsrfToken.as_view(),
        name='get-csrf-token'
    ),
    path(
        'health/',
        views.HealthCheck.as_view(),
        name='health'
    )
]
