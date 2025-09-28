import asyncio
from typing import Dict
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from shotclock.clock import SESSIONS, State

# Single-process ticker registry to avoid multiple loops per game_id
TICKERS: Dict[str, bool] = {}
INDEX_TICKER_ACTIVE = False


async def start_ticker(channel_layer, group_name, game_id, hz=10):
    interval = 1 / hz
    while TICKERS.get(game_id):
        st = SESSIONS.setdefault(game_id, State())
        payload = {
            "type": "tick",
            "remaining_ms": st.remaining_ms(),
            "running": st.running,
        }
        await channel_layer.group_send(
            group_name, {"type": "tick.message", "payload": payload}
        )
        await asyncio.sleep(interval)


async def start_index_ticker(channel_layer, hz=2):
    """Ticker for broadcasting all active clocks to index page clients"""
    global INDEX_TICKER_ACTIVE
    interval = 1 / hz
    while INDEX_TICKER_ACTIVE:
        # Collect all active clocks data
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

        payload = {
            "type": "clocks_update",
            "active_clocks": active_clocks,
            "count": len(active_clocks),
        }

        await channel_layer.group_send(
            "index_clients", {"type": "clocks.update", "payload": payload}
        )
        await asyncio.sleep(interval)


class IndexConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for the index page to receive live clock updates"""

    async def connect(self):
        global INDEX_TICKER_ACTIVE
        await self.channel_layer.group_add("index_clients", self.channel_name)
        await self.accept()

        # Send immediate snapshot
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

        active_clocks.sort(key=lambda x: x["game_id"])

        await self.send_json(
            {
                "type": "clocks_update",
                "active_clocks": active_clocks,
                "count": len(active_clocks),
            }
        )

        # Start index ticker if not already running
        if not INDEX_TICKER_ACTIVE:
            INDEX_TICKER_ACTIVE = True
            asyncio.create_task(start_index_ticker(self.channel_layer, hz=10))

    async def disconnect(self, code):
        await self.channel_layer.group_discard("index_clients", self.channel_name)
        # Note: For simplicity, we keep the ticker running even if no clients
        # Could be made to stop when last client disconnects

    async def clocks_update(self, event):
        """Handle clocks update messages from the ticker"""
        await self.send_json(event["payload"])


class ClockConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        url_route = self.scope.get("url_route", {})
        kwargs = url_route.get("kwargs", {})
        self.game_id = kwargs.get("game_id", "default")
        self.group_name = f"clock_{self.game_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Immediate snapshot
        st = SESSIONS.setdefault(self.game_id, State())
        await self.send_json(
            {"type": "tick", "remaining_ms": st.remaining_ms(), "running": st.running}
        )

        # Start ticker once per game_id
        if not TICKERS.get(self.game_id):
            TICKERS[self.game_id] = True
            asyncio.create_task(
                start_ticker(self.channel_layer, self.group_name, self.game_id, hz=10)
            )

    async def receive_json(self, content, **kwargs):
        st = SESSIONS.setdefault(self.game_id, State())
        cmd = content.get("cmd")
        if cmd == "start":
            st.start()
        elif cmd == "stop":
            st.stop()
        elif cmd == "reset":
            st.reset()
        elif cmd == "set":
            try:
                st.reset(int(content.get("value", st.length_ms)))
            except (TypeError, ValueError):
                pass

    async def tick_message(self, event):
        await self.send_json(event["payload"])

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        # If no one is left in the group, ticker could be stopped. For simplicity, keep it running
        # until process exit. To stop it when last client leaves, group size tracking would be needed.
