"""Command-line interface for TinyBoard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .domain import (
    DuplicateActiveTitleError,
    InvalidTitleError,
    Task,
    allocate_id,
    title_key,
)
from .persistence import PersistenceError, load_tasks, save_tasks


DEFAULT_DATABASE = ".tinyboard.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tinyboard")
    parser.add_argument(
        "--version",
        action="version",
        version=f"tinyboard {__version__}",
    )
    parser.add_argument("--db", default=DEFAULT_DATABASE, help="database path")
    commands = parser.add_subparsers(dest="command")

    add_parser = commands.add_parser("add")
    add_parser.add_argument("title")
    commands.add_parser("list")

    complete_parser = commands.add_parser("complete")
    complete_parser.add_argument("id", type=int)

    archive_parser = commands.add_parser("archive")
    archive_parser.add_argument("id", type=int)
    commands.add_parser("summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.error("a command is required")

    try:
        tasks = load_tasks(Path(args.db))
        if args.command == "add":
            requested_key = title_key(args.title)
            duplicate = next(
                (
                    task for task in tasks
                    if not task.completed
                    and not task.archived
                    and title_key(task.title) == requested_key
                ),
                None,
            )
            if duplicate is not None:
                raise DuplicateActiveTitleError(
                    f"an active task already exists with title: {duplicate.title}"
                )
            task = Task.create(allocate_id(tasks), args.title)
            tasks.append(task)
            save_tasks(args.db, tasks)
            print(f"added {task.id}\t{task.title}")
        elif args.command == "list":
            for task in sorted(
                (task for task in tasks if not task.archived),
                key=lambda task: task.id,
            ):
                marker = "x" if task.completed else " "
                print(f"{task.id}\t[{marker}]\t{task.title}")
        elif args.command == "complete":
            task = next((task for task in tasks if task.id == args.id), None)
            if task is None:
                parser.error(f"unknown task ID: {args.id}")
            task.completed = True
            save_tasks(args.db, tasks)
            print(f"completed {task.id}")
        elif args.command == "archive":
            task = next((task for task in tasks if task.id == args.id), None)
            if task is None:
                parser.error(f"unknown task ID: {args.id}")
            if not task.completed:
                raise ValueError(f"cannot archive incomplete task: {task.id}")
            task.archived = True
            save_tasks(args.db, tasks)
            print(f"archived {task.id}")
        else:
            active = sum(
                not task.completed and not task.archived for task in tasks
            )
            completed = sum(
                task.completed and not task.archived for task in tasks
            )
            archived = sum(task.archived for task in tasks)
            print(json.dumps({
                "total": len(tasks),
                "active": active,
                "completed": completed,
                "archived": archived,
            }, separators=(",", ":")))
    except (InvalidTitleError, PersistenceError, OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0
