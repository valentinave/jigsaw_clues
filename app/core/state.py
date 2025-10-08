from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Iterable

from .timer import CountdownTimer, TimerSnapshot
from .websocket_manager import WebSocketManager
from ..data import ROOM_GROUPS, all_games
from ..models.game import GameState


class AppState:
    def __init__(self, ws_manager: WebSocketManager) -> None:
        self.ws = ws_manager
        self.timer = CountdownTimer(on_tick=self._on_timer_tick)
        self._games: Dict[str, GameState] = {game.id: GameState(game=game) for game in all_games()}
        self._log: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def full_state(self) -> dict[str, Any]:
        async with self._lock:
            puzzles = [state.to_dict for state in self._games.values()]
            log = list(self._log)
        timer_snapshot = self.timer.snapshot()
        return {
            "timer": timer_snapshot.formatted,
            "timer_running": timer_snapshot.running,
            "puzzles": puzzles,
            "log": log,
            "rooms": {
                key: {"label": data["label"], "targets": data["targets"]}
                for key, data in ROOM_GROUPS.items()
            },
        }

    async def mark_solved(self, puzzle_id: str, solved: bool) -> dict[str, Any]:
        async with self._lock:
            state = self._games[puzzle_id]
            state.solved = solved
            state.solve_timestamp = time.time() if solved else None
            payload = state.to_dict
        await self.ws.broadcast({"type": "puzzle", "data": payload})
        self.add_log(f"Puzzle {payload['label']} marked {'solved' if solved else 'unsolved'}")
        return payload

    async def increment_hint(self, puzzle_id: str, delta: int = 1) -> dict[str, Any]:
        async with self._lock:
            state = self._games[puzzle_id]
            state.hints_used = max(0, state.hints_used + int(delta))
            payload = state.to_dict
        await self.ws.broadcast({"type": "puzzle", "data": payload})
        self.add_log(f"Hints for {payload['label']} set to {payload['hints_used']}")
        return payload

    async def set_hints(self, puzzle_id: str, value: int) -> dict[str, Any]:
        async with self._lock:
            state = self._games[puzzle_id]
            state.hints_used = max(0, int(value))
            payload = state.to_dict
        await self.ws.broadcast({"type": "puzzle", "data": payload})
        self.add_log(f"Hints for {payload['label']} set to {payload['hints_used']}")
        return payload

    def add_log(self, message: str, *, kind: str = "info") -> None:
        entry = {"ts": time.time(), "message": message, "kind": kind}
        self._log.append(entry)
        self._log = self._log[-400:]
        asyncio.create_task(self.ws.broadcast({"type": "log", "data": entry}))

    def game_state(self, puzzle_id: str) -> GameState:
        return self._games[puzzle_id]

    async def timer_action(self, action: str, value: int | None = None) -> TimerSnapshot:
        action = action.lower()
        if action == "start":
            snapshot = await self.timer.start()
            self.add_log("Timer started")
        elif action == "pause":
            snapshot = await self.timer.pause()
            self.add_log("Timer paused")
        elif action == "reset":
            seconds = value or 0
            snapshot = await self.timer.reset(seconds)
            self.add_log(f"Timer reset to {snapshot.formatted}")
        elif action == "set":
            if value is None:
                raise ValueError("Set action requires a value")
            snapshot = await self.timer.set_seconds(value)
            self.add_log(f"Timer set to {snapshot.formatted}")
        elif action == "add":
            if value is None:
                raise ValueError("Add action requires a value")
            snapshot = await self.timer.add_seconds(value)
            sign = "+" if value >= 0 else ""
            self.add_log(f"Timer adjusted by {sign}{value}s → {snapshot.formatted}")
        else:
            raise ValueError(f"Unknown timer action: {action}")
        return snapshot

    async def timer_tick_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(1)
                snapshot = await self.timer.tick()
                if snapshot.running and snapshot.seconds == 0:
                    self.add_log("Timer completed", kind="success")
        except asyncio.CancelledError:  # pragma: no cover - shutdown path
            return

    def _on_timer_tick(self, snapshot: TimerSnapshot) -> None:
        asyncio.create_task(self.ws.broadcast({"type": "timer", "data": {
            "formatted": snapshot.formatted,
            "running": snapshot.running,
        }}))

    def puzzles_for_room(self, room_key: str) -> Iterable[dict[str, Any]]:
        return [state.to_dict for state in self._games.values() if state.game.room.lower().replace(" ", "") == room_key]
