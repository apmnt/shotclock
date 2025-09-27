from django.urls import re_path
from shotclock import consumers

websocket_urlpatterns = [
    re_path(r"ws/clock/(?P<game_id>[\w-]+)/$", consumers.ClockConsumer.as_asgi()),  # type: ignore
]
