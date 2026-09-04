"""
ASGI config for midiranger project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'midiranger.settings')

# Muss vor jedem Import, der Django-Modelle berührt (z.B. app.routing ->
# app.consumers), aufgerufen werden, damit die App-Registry bereit ist.
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from app.routing import websocket_urlpatterns

# WebSocket ist der Ersatz für Qt's Cross-Thread-Signal-Zustellung an die UI
# (Statusleiste/Play-Icon reagieren auf "Song von selbst zu Ende" ohne Reload).
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
