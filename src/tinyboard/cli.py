"""Command-line interface for TinyBoard."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .domain import InvalidTitleError, Task, allocate_id
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.error("a command is required")

    try:
        tasks = load_tasks(Path(args.db))
        if args.command == "add":
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
        else:
            task = next((task for task in tasks if task.id == args.id), None)
            if task is None:
                parser.error(f"unknown task ID: {args.id}")
            task.completed = True
            save_tasks(args.db, tasks)
            print(f"completed {task.id}")
    except (InvalidTitleError, PersistenceError, OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0
