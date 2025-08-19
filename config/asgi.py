import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()


from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from chat.middlewares import JwtAuthTokenMiddleware
from chat.routing import websocket_urlpatterns


application = ProtocolTypeRouter({
    "http": application,
    "websocket": JwtAuthTokenMiddleware(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    )
})
