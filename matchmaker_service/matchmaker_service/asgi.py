import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

import matchmaker_app.routing


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matchmaker_service.settings")
django_asgi_app = get_asgi_application()
websocket_patterns = matchmaker_app.routing.get_websocket_urlpatterns()
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_patterns))
        ),
    }
)
