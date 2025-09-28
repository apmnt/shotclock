from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.urls import reverse
import time
from shotclock.clock import SESSIONS, State


def index(request):
    """Main index page showing available options"""
    # Get all active clock sessions
    active_clocks = []
    for game_id, state in SESSIONS.items():
        ms = state.remaining_ms()
        mins, secs = divmod(ms // 1000, 60)
        tenths = (ms % 1000) // 100
        time_display = f"{mins:02d}:{secs:02d}.{tenths}"

        active_clocks.append(
            {
                "game_id": game_id,
                "time_display": time_display,
                "remaining_ms": ms,
                "running": state.running,
                "status": "Running" if state.running else "Stopped",
            }
        )

    # Sort by game_id for consistent display
    active_clocks.sort(key=lambda x: x["game_id"])

    return render(request, "shotclock/index.html", {"active_clocks": active_clocks})


def control(request, game_id):
    return render(request, "shotclock/control.html", {"game_id": game_id})


def display(request, game_id):
    return render(request, "shotclock/display.html", {"game_id": game_id})


def state_json(request, game_id):
    st = SESSIONS.setdefault(game_id, State())
    return JsonResponse({"remaining_ms": st.remaining_ms(), "running": st.running})


def state_plain(request, game_id):
    st = SESSIONS.setdefault(game_id, State())
    ms = st.remaining_ms()
    mins, secs = divmod(ms // 1000, 60)
    tenths = (ms % 1000) // 100
    return HttpResponse(
        f"{mins:02d}:{secs:02d}.{tenths}|{int(st.running)}", content_type="text/plain"
    )


def stream_sse(request, game_id):
    def gen():
        while True:
            st = SESSIONS.setdefault(game_id, State())
            ms = st.remaining_ms()
            data = f'{{"remaining_ms":{ms},"running":{str(st.running).lower()}}}'
            yield f"data: {data}\n\n".encode("utf-8")
            time.sleep(0.2)  # ~5 Hz

    resp = StreamingHttpResponse(gen(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    return resp


def all_clocks_json(request):
    """API endpoint to get all active clocks and their states"""
    clocks = {}
    for game_id, state in SESSIONS.items():
        clocks[game_id] = {
            "remaining_ms": state.remaining_ms(),
            "running": state.running,
            "length_ms": state.length_ms,
        }
    return JsonResponse({"clocks": clocks, "count": len(clocks)})
