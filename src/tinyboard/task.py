"""Domain model for TinyBoard tasks."""

from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Iterable


_WHITESPACE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    """Return *title* with surrounding and repeated whitespace normalized."""
    if not isinstance(title, str):
        raise TypeError("title must be a string")

    normalized = _WHITESPACE.sub(" ", title.strip())
    if not normalized:
        raise ValueError("title must not be empty")
    return normalized


@dataclass
class Task:
    """A TinyBoard task and its domain state."""

    id: int
    title: str
    completed: bool = False
    archived: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.id, bool) or not isinstance(self.id, int) or self.id <= 0:
            raise ValueError("id must be a positive integer")
        self.title = normalize_title(self.title)
        if not isinstance(self.completed, bool):
            raise TypeError("completed must be a boolean")
        if not isinstance(self.archived, bool):
            raise TypeError("archived must be a boolean")

    @classmethod
    def new(cls, task_id: int, title: str) -> "Task":
        """Create a new, incomplete and unarchived task."""
        return cls(task_id, normalize_title(title))


def next_task_id(existing: Iterable[Task | int]) -> int:
    """Allocate the next ID after the greatest existing ID."""
    ids = (item.id if isinstance(item, Task) else item for item in existing)
    return max(ids, default=0) + 1


class TaskIdAllocator:
    """Reusable stateful allocator for a collection of existing task IDs."""

    def __init__(self, existing: Iterable[Task | int] = ()) -> None:
        self._next_id = next_task_id(existing)

    def allocate(self) -> int:
        task_id = self._next_id
        self._next_id += 1
        return task_id
