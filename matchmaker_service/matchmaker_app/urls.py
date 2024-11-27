from django.urls import path

from .views.games import (
    GamesView, MyGamesView, GameDetailView, GameResultView, GameStartView
)
from .views.misc import getCsrfToken, HealthCheck
from .views.players import (
    PlayersView, PlayerDetailView, PlayerStatsView
)
from .views.tournaments import (
    TournamentsView, MyTournamentsView, TournamentDetailView
)


# API Endpoints
# -------------
# GET  /api/games/                     : List all games
#                                    ?status=<game_status>      # Optional
#                                    ?type=<game_type>          # Optional
#                                    ?player=<player_name>      # Optional
#                                    ?opponent=<opponent_name>  # Optional
#                                    ?joined=<bool>             # Optional
#                                    ?limit=<last_n_games>      # Optional
#
# POST /api/games/                     : Register a game
#                                       {
#                                           "player1": str,  # Optional
#                                           "player2": str   # Optional
#                                           "type": str      # Optional
#                                       }
#
# GET  /api/games/me/                  : List games with logged in user
#                                    ?joined=<bool>         # Optional
#                                    ?status=<game_status>  # Optional
#
# GET  /api/games/<game_id>/           : Get details of a game
#
# PUT  /api/games/<game_id>/           : Join a game
#                                       {
#                                           "player": str    # Optional
#                                       }
#
# DELETE /api/games/<game_id>/         : Delete a game
#
# PUT  /api/games/start/<game_id>/     : Request the start of a game from
#                                       game-service
#
# POST /api/games/result/             : Submit the result of a game
#                                       {
#                                           "game_id": int,     # Required
#                                           "left_score": int,  # Required
#                                           "right_score": int  # Required
#                                       }
#
# GET  /api/tournaments/               : List all tournaments
#                                     ?status=<tournament_status>  # Optional
#                                     ?type=<tournament_type>      # Optional
#                                     ?player=<player_name>        # Optional
#                                     ?limit=<last_n_tournaments>  # Optional
#
# POST /api/tournaments/               : Create a new tournament
#                                       {
#                                           "pool_size": int,       # Required
#                                           "tournament_name": str, # Optional
#                                           "players": [str]        # Optional
#                                           "type": str             # Optional
#                                       }
#
# GET /api/tournaments/me/            : List tournaments with logged in user
#                                    ?status=<tournament_status>  # Optional
#
# GET  /api/tournaments/<tournament_id>/  : Get details of a tournament
#
# POST  /api/tournaments/<tournament_id>/ : Join a tournament
#                                       {
#                                           "player": str    # Optional
#                                       }
#
# DELETE /api/tournaments/<tournament_id>/ : Leave a tournament
#                                       {
#                                           "player": str    # Optional
#                                       }
#
# GET  /api/players/                   : List all players
#
# POST /api/players/                   : Register a player
#                                       {
#                                           "name": str,       # Required
#                                       }
#
# GET  /api/players/<player_name>/     : Get details of a player
#
# PATCH /api/players/<player_name>/    : Update a player
#                                       {
#                                           <field>: <value>  # one or more
#                                       }
#
# GET  /api/players/<player_name>/stats/ : Game details and stats of a player
#                                       ?opponent=<opponent_name>   # Optional
#                                       ?position=<player_position> # Optional
#                                       ?status=<game_status>       # Optional
#                                       ?limit=<last_n_games>       # Optional
#
# GET  /get-csrf-token/                : Get CSRF token
#
# GET  /health/                        : Health check

urlpatterns = [
    path(
        'api/games/',
        GamesView.as_view(),
        name='games'
    ),
    path(
        'api/games/me/',
        MyGamesView.as_view(),
        name='my-games'
    ),
    path(
        'api/games/result/',
        GameResultView.as_view(),
        name='game-result'
    ),
    path(
        'api/games/<str:game_id>/',
        GameDetailView.as_view(),
        name='games-detail'
    ),
    path(
        'api/games/start/<str:game_id>/',
        GameStartView.as_view(),
        name='game-start'
    ),
    path(
        'api/tournaments/',
        TournamentsView.as_view(),
        name='tournaments'
    ),
    path(
        'api/tournaments/me/',
        MyTournamentsView.as_view(),
        name='my-tournaments'
    ),
    path(
        'api/tournaments/<str:tournament_id>/',
        TournamentDetailView.as_view(),
        name='tournaments-detail'
    ),
    path(
        'api/players/',
        PlayersView.as_view(),
        name='players'
    ),
    path(
        'api/players/<str:player_name>/',
        PlayerDetailView.as_view(),
        name='players-detail'
    ),
    path(
        'api/players/<str:player_name>/stats/',
        PlayerStatsView.as_view(),
        name='players-stats'
    ),
    path(
        'get-csrf-token/',
        getCsrfToken.as_view(),
        name='get-csrf-token'
    ),
    path(
        'health/',
        HealthCheck.as_view(),
        name='health'
    ),
]
