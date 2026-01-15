from django.urls import path
from backend import consumers

websocket_urlpatterns = [
    path(r'ws/', consumers.WebSocket.as_asgi()),
]
