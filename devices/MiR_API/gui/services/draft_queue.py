"""Local draft action queue — not the robot mission_queue until Start runs."""

from __future__ import annotations

from gui.models import QueueAction


class DraftQueue:
    def __init__(self) -> None:
        self._items: list[QueueAction] = []

    def __len__(self) -> int:
        return len(self._items)

    def items(self) -> list[QueueAction]:
        return list(self._items)

    def add(self, action: QueueAction) -> None:
        self._items.append(action)

    def remove_at(self, index: int) -> QueueAction | None:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def remove_uid(self, uid: str) -> QueueAction | None:
        for i, item in enumerate(self._items):
            if item.uid == uid:
                return self._items.pop(i)
        return None

    def clear(self) -> None:
        self._items.clear()

    def move(self, from_index: int, to_index: int) -> bool:
        if from_index == to_index:
            return False
        if not (0 <= from_index < len(self._items)):
            return False
        if not (0 <= to_index < len(self._items)):
            return False
        item = self._items.pop(from_index)
        self._items.insert(to_index, item)
        return True

    def move_up(self, index: int) -> bool:
        if index <= 0:
            return False
        return self.move(index, index - 1)

    def move_down(self, index: int) -> bool:
        if index < 0 or index >= len(self._items) - 1:
            return False
        return self.move(index, index + 1)
