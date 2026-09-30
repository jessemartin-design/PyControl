"""GUI-side models (no HTTP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class ActionKind(str, Enum):
    POSITION = "position"
    MISSION = "mission"


@dataclass(frozen=True)
class QueueAction:
    """One draft-queue entry: either a named position or a named mission."""

    kind: ActionKind
    name: str
    guid: str
    uid: str = field(default_factory=lambda: uuid4().hex)

    def label(self) -> str:
        prefix = "GoTo" if self.kind is ActionKind.POSITION else "Mission"
        return f"{prefix}: {self.name}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "name": self.name,
            "guid": self.guid,
            "uid": self.uid,
        }


class RunnerState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
