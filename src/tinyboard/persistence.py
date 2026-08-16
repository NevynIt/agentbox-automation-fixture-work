"""Versioned JSON persistence for TinyBoard tasks."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from collections.abc import Iterable

from .domain import Task


class PersistenceError(ValueError):
    """Raised when a TinyBoard database cannot be read or written."""


SCHEMA_VERSION = 1


def load_tasks(path: str | os.PathLike[str]) -> list[Task]:
    """Load tasks from *path*, treating a missing database as an empty board."""
    database = Path(path)
    if not database.exists():
        return []

    try:
        with database.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise PersistenceError(f"could not load database {database}: {exc}") from exc

    if not isinstance(data, dict):
        raise PersistenceError("database must contain a JSON object")
    version = data.get("version")
    if version != SCHEMA_VERSION or isinstance(version, bool):
        raise PersistenceError(
            f"unsupported database schema version: {version!r}"
        )
    records = data.get("tasks")
    if not isinstance(records, list):
        raise PersistenceError("database field 'tasks' must be a JSON array")

    tasks: list[Task] = []
    ids: set[int] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise PersistenceError(f"task at index {index} must be a JSON object")
        required = {"id", "title", "completed", "archived"}
        if set(record) != required:
            raise PersistenceError(
                f"task at index {index} must contain exactly {sorted(required)!r}"
            )
        try:
            task = Task(**record)
        except (TypeError, ValueError) as exc:
            raise PersistenceError(f"invalid task at index {index}: {exc}") from exc
        if task.id in ids:
            raise PersistenceError(f"duplicate task id: {task.id}")
        ids.add(task.id)
        tasks.append(task)
    return tasks


def save_tasks(path: str | os.PathLike[str], tasks: Iterable[Task]) -> None:
    """Atomically save *tasks* as version 1 JSON, creating its parent if needed."""
    database = Path(path)
    parent = database.parent
    parent.mkdir(parents=True, exist_ok=True)
    records = []
    for task in tasks:
        if not isinstance(task, Task):
            raise TypeError("tasks must contain Task instances")
        records.append(
            {
                "id": task.id,
                "title": task.title,
                "completed": task.completed,
                "archived": task.archived,
            }
        )
    data = {"version": SCHEMA_VERSION, "tasks": records}

    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=parent, prefix=f".{database.name}.",
            delete=False
        ) as stream:
            temporary_name = stream.name
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, database)
        temporary_name = None
    except OSError as exc:
        raise PersistenceError(f"could not save database {database}: {exc}") from exc
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


load = load_tasks
save = save_tasks
