from django.urls import re_path


def get_websocket_urlpatterns():
    from .consumers import MatchmakerConsumer
    return [
        re_path(r'^ws/connect/?$', MatchmakerConsumer.as_asgi()),
    ]
