from django.urls import re_path
from apps import consumers
from apps.consumers import StudentScoreConsumer

websocket_urlpatterns = [
    # re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
    # re_path(r"ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
    re_path(r"ws/dashboard/$", StudentScoreConsumer.as_asgi())
]