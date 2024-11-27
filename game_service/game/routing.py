from django.urls import re_path


def get_websocket_urlpatterns():
    from .consumers import GamePlayerConsumer
    return [
        re_path(
            r"^ws/game/(?P<game_id>[\w-]+)/$", GamePlayerConsumer.as_asgi()
        )
    ]
