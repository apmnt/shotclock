import asyncio
from typing import Dict
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from shotclock.clock import SESSIONS, State

# Single-process ticker registry to avoid multiple loops per game_id
TICKERS: Dict[str, bool] = {}


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
