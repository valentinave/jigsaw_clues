from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class TimerSnapshot:
    seconds: int
    running: bool

    @property
    def formatted(self) -> str:
        total = max(0, self.seconds)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class CountdownTimer:
    """Lightweight countdown timer with async tick notifications."""

    def __init__(self, *, on_tick: Callable[[TimerSnapshot], None] | None = None):
        self._remaining_seconds: int = 0
        self._running: bool = False
        self._last_start_monotonic: float | None = None
        self._lock = asyncio.Lock()
        self._on_tick = on_tick
        self._last_broadcast_seconds: int | None = None
        self._last_broadcast_running: bool | None = None

    async def reset(self, seconds: int = 0) -> TimerSnapshot:
        async with self._lock:
            self._remaining_seconds = max(0, int(seconds))
            self._running = False
            self._last_start_monotonic = None
            snapshot = self._snapshot()
        self._emit(snapshot)
        return snapshot

    async def set_seconds(self, seconds: int) -> TimerSnapshot:
        async with self._lock:
            self._remaining_seconds = max(0, int(seconds))
            if self._running:
                self._last_start_monotonic = time.monotonic()
            snapshot = self._snapshot()
        self._emit(snapshot)
        return snapshot

    async def add_seconds(self, delta: int) -> TimerSnapshot:
        async with self._lock:
            if self._running:
                self._sync_locked()
            self._remaining_seconds = max(0, self._remaining_seconds + int(delta))
            snapshot = self._snapshot()
        self._emit(snapshot)
        return snapshot

    async def start(self) -> TimerSnapshot:
        async with self._lock:
            if self._remaining_seconds <= 0:
                self._remaining_seconds = 0
                self._running = False
            elif not self._running:
                self._running = True
                self._last_start_monotonic = time.monotonic()
            snapshot = self._snapshot()
        self._emit(snapshot)
        return snapshot

    async def pause(self) -> TimerSnapshot:
        async with self._lock:
            if self._running:
                self._sync_locked()
                self._running = False
            snapshot = self._snapshot()
        self._emit(snapshot)
        return snapshot

    async def tick(self) -> TimerSnapshot:
        async with self._lock:
            if self._running:
                self._sync_locked()
                if self._remaining_seconds <= 0:
                    self._remaining_seconds = 0
                    self._running = False
            snapshot = self._snapshot()
        self._emit(snapshot)
        return snapshot

    def _sync_locked(self) -> None:
        if not self._running or self._last_start_monotonic is None:
            return
        elapsed = int(time.monotonic() - self._last_start_monotonic)
        if elapsed <= 0:
            return
        self._remaining_seconds = max(0, self._remaining_seconds - elapsed)
        self._last_start_monotonic = time.monotonic()

    def _snapshot(self) -> TimerSnapshot:
        if self._running and self._last_start_monotonic is not None:
            elapsed = int(time.monotonic() - self._last_start_monotonic)
            remaining = max(0, self._remaining_seconds - elapsed)
        else:
            remaining = max(0, self._remaining_seconds)
        return TimerSnapshot(seconds=remaining, running=self._running and remaining > 0)

    def _emit(self, snapshot: TimerSnapshot) -> None:
        if not self._on_tick:
            return
        if (
            self._last_broadcast_seconds == snapshot.seconds
            and self._last_broadcast_running == snapshot.running
        ):
            return
        self._on_tick(snapshot)
        self._last_broadcast_seconds = snapshot.seconds
        self._last_broadcast_running = snapshot.running

    def snapshot(self) -> TimerSnapshot:
        return self._snapshot()
