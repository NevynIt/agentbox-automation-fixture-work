"""Versioned JSON persistence for TinyBoard tasks."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from collections.abc import Iterable

from .task import Task


SCHEMA_VERSION = 1
_TASK_FIELDS = {"id", "title", "completed", "archived"}


class PersistenceError(ValueError):
    """Raised when a TinyBoard database cannot be read or written."""


def load_tasks(path: str | os.PathLike[str]) -> list[Task]:
    """Load tasks from *path*, treating a missing file as an empty board."""
    database_path = Path(path)
    try:
        with database_path.open("r", encoding="utf-8") as database_file:
            document = json.load(database_file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        raise PersistenceError(
            f"invalid JSON in TinyBoard database {database_path}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise PersistenceError(
            f"could not read TinyBoard database {database_path}: {exc}"
        ) from exc

    if not isinstance(document, dict):
        raise PersistenceError("TinyBoard database must contain a JSON object")
    version = document.get("version")
    if isinstance(version, bool) or not isinstance(version, int):
        raise PersistenceError("TinyBoard database version must be integer 1")
    if version != SCHEMA_VERSION:
        raise PersistenceError(
            f"unsupported TinyBoard database version: {version}"
        )

    records = document.get("tasks")
    if not isinstance(records, list):
        raise PersistenceError("TinyBoard database tasks must be a JSON array")

    tasks: list[Task] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise PersistenceError(f"task at index {index} must be a JSON object")
        if set(record) != _TASK_FIELDS:
            raise PersistenceError(
                f"task at index {index} must contain exactly: id, title, completed, archived"
            )
        try:
            tasks.append(Task(**record))
        except (TypeError, ValueError) as exc:
            raise PersistenceError(
                f"invalid task at index {index}: {exc}"
            ) from exc
    return tasks


def save_tasks(path: str | os.PathLike[str], tasks: Iterable[Task]) -> None:
    """Atomically save *tasks* to *path* in the version-1 JSON format."""
    database_path = Path(path)
    parent = database_path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise PersistenceError(
            f"could not create TinyBoard database directory {parent}: {exc}"
        ) from exc

    records = []
    for index, task in enumerate(tasks):
        if not isinstance(task, Task):
            raise PersistenceError(f"item at index {index} is not a Task")
        records.append(
            {
                "id": task.id,
                "title": task.title,
                "completed": task.completed,
                "archived": task.archived,
            }
        )
    document = {"version": SCHEMA_VERSION, "tasks": records}

    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=parent,
            prefix=f".{database_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(document, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, database_path)
        temporary_path = None
    except (OSError, TypeError, ValueError) as exc:
        raise PersistenceError(
            f"could not save TinyBoard database {database_path}: {exc}"
        ) from exc
    finally:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


class JsonPersistence:
    """Path-bound convenience wrapper around :func:`load_tasks` and save_tasks."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)

    def load(self) -> list[Task]:
        return load_tasks(self.path)

    def save(self, tasks: Iterable[Task]) -> None:
        save_tasks(self.path, tasks)

