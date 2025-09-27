from django.urls import path
from shotclock import views

urlpatterns = [
    path("", views.index, name="index"),
    path("control/<slug:game_id>/", views.control, name="control"),
    path("display/<slug:game_id>/", views.display, name="display"),
    # REST/SSE
    path("api/clock/<slug:game_id>/state", views.state_json, name="state_json"),
    path("api/clock/<slug:game_id>/state.txt", views.state_plain, name="state_plain"),
    path("api/clock/<slug:game_id>/stream", views.stream_sse, name="state_sse"),
]
