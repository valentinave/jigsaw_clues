from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(slots=True)
class Game:
    id: str
    label: str
    room: str
    video: str
    default_targets: Sequence[str]
    description: str | None = None


@dataclass(slots=True)
class GameState:
    game: Game
    solved: bool = False
    hints_used: int = 0
    solve_timestamp: float | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.game.id,
            "label": self.game.label,
            "room": self.game.room,
            "room_key": self.game.room.lower().replace(" ", ""),
            "video": self.game.video,
            "targets": list(self.game.default_targets),
            "solved": self.solved,
            "hints_used": self.hints_used,
            "solve_timestamp": self.solve_timestamp,
            "notes": list(self.notes),
        }
