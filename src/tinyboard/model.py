"""Small, dependency-free TinyBoard domain model."""

from __future__ import annotations

from dataclasses import dataclass


def normalize_title(title: str) -> str:
    normalized = " ".join(title.split())
    if not normalized:
        raise ValueError("title must not be empty")
    return normalized


@dataclass
class Task:
    id: int
    title: str
    completed: bool = False
    archived: bool = False

    @classmethod
    def create(cls, identifier: int, title: str) -> "Task":
        if identifier <= 0:
            raise ValueError("task id must be positive")
        return cls(identifier, normalize_title(title))

    @property
    def active(self) -> bool:
        return not self.completed and not self.archived

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "title": self.title,
                "completed": self.completed, "archived": self.archived}

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "Task":
        if not isinstance(value.get("id"), int) or isinstance(value["id"], bool):
            raise ValueError("task id must be an integer")
        if not isinstance(value.get("title"), str):
            raise ValueError("task title must be a string")
        completed = value.get("completed", False)
        archived = value.get("archived", False)
        if not isinstance(completed, bool) or not isinstance(archived, bool):
            raise ValueError("task state must be boolean")
        return cls(value["id"], normalize_title(value["title"]), completed, archived)


def duplicate_key(title: str) -> str:
    return normalize_title(title).casefold()
