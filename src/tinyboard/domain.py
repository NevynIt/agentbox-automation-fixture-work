"""Core task domain model for TinyBoard."""

from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Iterable


class InvalidTitleError(ValueError):
    """Raised when a task title is empty after normalization."""


class DuplicateActiveTitleError(ValueError):
    """Raised when an active task already has the requested title key."""


def normalize_title(title: str) -> str:
    """Trim a title and collapse all internal whitespace to ASCII spaces."""
    if not isinstance(title, str):
        raise TypeError("title must be a string")
    return re.sub(r"\s+", " ", title.strip())


def title_key(title: str) -> str:
    """Return the normalized, case-insensitive comparison key for a title."""
    return normalize_title(title).casefold()


@dataclass
class Task:
    """A TinyBoard task and its lifecycle state."""

    id: int
    title: str
    completed: bool = False
    archived: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.id, int) or isinstance(self.id, bool) or self.id <= 0:
            raise ValueError("id must be a positive integer")
        self.title = normalize_title(self.title)
        if not self.title:
            raise InvalidTitleError("title must not be empty")
        if not isinstance(self.completed, bool):
            raise TypeError("completed must be a boolean")
        if not isinstance(self.archived, bool):
            raise TypeError("archived must be a boolean")

    @classmethod
    def create(cls, id: int, title: str) -> "Task":
        """Construct a new, incomplete, unarchived task."""
        return cls(id=id, title=title)


def allocate_id(tasks: Iterable[Task]) -> int:
    """Return the next ID after the maximum existing task ID.

    Missing IDs are intentionally not reused.
    """
    highest = 0
    for task in tasks:
        task_id = task.id if isinstance(task, Task) else task
        if not isinstance(task_id, int) or isinstance(task_id, bool) or task_id <= 0:
            raise ValueError("existing task IDs must be positive integers")
        highest = max(highest, task_id)
    return highest + 1
