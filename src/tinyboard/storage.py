"""Versioned JSON persistence with atomic same-directory replacement."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from .model import Task, duplicate_key


class StorageError(ValueError):
    pass


class Board:
    def __init__(self, path: Path):
        self.path = path
        self.tasks: list[Task] = []

    @classmethod
    def load(cls, path: Path) -> "Board":
        board = cls(path)
        if not path.exists():
            return board
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"invalid database: {path}") from exc
        if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("tasks"), list):
            raise StorageError("unsupported or malformed database schema")
        try:
            board.tasks = [Task.from_dict(item) for item in data["tasks"]]
        except (TypeError, ValueError) as exc:
            raise StorageError(f"invalid task data: {exc}") from exc
        return board

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "tasks": [task.to_dict() for task in self.tasks]}
        fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def add(self, title: str) -> Task:
        key = duplicate_key(title)
        if any(task.active and duplicate_key(task.title) == key for task in self.tasks):
            raise ValueError("an active task with that title already exists")
        task = Task.create(max((item.id for item in self.tasks), default=0) + 1, title)
        self.tasks.append(task)
        self.save()
        return task
