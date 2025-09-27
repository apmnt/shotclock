import time
from dataclasses import dataclass
from typing import Dict

@dataclass
class State:
    length_ms: int = 24000
    running: bool = False
    started_mono: float | None = None
    remaining_ms_paused: int = 24000

    def remaining_ms(self) -> int:
        if self.running and self.started_mono is not None:
            elapsed = (time.monotonic() - self.started_mono) * 1000
            return max(0, int(self.length_ms - elapsed))
        return self.remaining_ms_paused

    def start(self):
        if not self.running:
            # Back-calc start so remaining keeps continuity
            self.started_mono = time.monotonic() - (self.length_ms - self.remaining_ms_paused)/1000
            self.running = True

    def stop(self):
        if self.running:
            self.remaining_ms_paused = self.remaining_ms()
            self.running = False
            self.started_mono = None

    def reset(self, to_ms: int | None = None):
        if to_ms is not None:
            self.length_ms = to_ms
        self.remaining_ms_paused = self.length_ms
        self.started_mono = None
        self.running = False

# In-memory session per game_id (OK for single-process dev)
SESSIONS: Dict[str, State] = {}
