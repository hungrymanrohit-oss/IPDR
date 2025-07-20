"""
WebSocket routing for flows app.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/flows/$', consumers.FlowConsumer.as_asgi()),
    re_path(r'ws/alerts/$', consumers.AlertConsumer.as_asgi()),
]