"""Command-line interface for TinyBoard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .persistence import PersistenceError, load_tasks, save_tasks
from .task import Task, next_task_id, title_comparison_key


DEFAULT_DATABASE = ".tinyboard.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tinyboard")
    parser.add_argument(
        "--version",
        action="version",
        version=f"tinyboard {__version__}",
    )
    parser.add_argument("--db", default=DEFAULT_DATABASE, type=Path)
    commands = parser.add_subparsers(dest="command")

    add_parser = commands.add_parser("add")
    add_parser.add_argument("title")
    commands.add_parser("list")
    complete_parser = commands.add_parser("complete")
    complete_parser.add_argument("id", type=_task_id)
    archive_parser = commands.add_parser("archive")
    archive_parser.add_argument("id", type=_task_id)
    commands.add_parser("summary")
    return parser


def _task_id(value: str) -> int:
    try:
        task_id = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("ID must be a positive integer") from exc
    if task_id <= 0:
        raise argparse.ArgumentTypeError("ID must be a positive integer")
    return task_id


def _run_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    try:
        tasks = load_tasks(args.db)
        if args.command == "add":
            comparison_key = title_comparison_key(args.title)
            duplicate = next(
                (
                    task
                    for task in tasks
                    if not task.completed
                    and not task.archived
                    and title_comparison_key(task.title) == comparison_key
                ),
                None,
            )
            if duplicate is not None:
                parser.error(
                    f"an active task with this title already exists (ID: {duplicate.id})"
                )
            task = Task.new(next_task_id(tasks), args.title)
            tasks.append(task)
            save_tasks(args.db, tasks)
            print(f"added {task.id}\t{task.title}")
            return 0

        if args.command == "list":
            for task in sorted(
                (task for task in tasks if not task.archived),
                key=lambda task: task.id,
            ):
                marker = "[x]" if task.completed else "[ ]"
                print(f"{task.id}\t{marker}\t{task.title}")
            return 0

        if args.command == "complete":
            task = next((task for task in tasks if task.id == args.id), None)
            if task is None:
                parser.error(f"unknown task ID: {args.id}")
            if not task.completed:
                task.completed = True
                save_tasks(args.db, tasks)
            print(f"completed {task.id}")
            return 0

        if args.command == "archive":
            task = next((task for task in tasks if task.id == args.id), None)
            if task is None:
                parser.error(f"unknown task ID: {args.id}")
            if not task.completed:
                parser.error(f"task {task.id} is incomplete and cannot be archived")
            if not task.archived:
                task.archived = True
                save_tasks(args.db, tasks)
            print(f"archived {task.id}")
            return 0

        if args.command == "summary":
            archived = sum(task.archived for task in tasks)
            completed = sum(task.completed and not task.archived for task in tasks)
            active = sum(not task.completed and not task.archived for task in tasks)
            print(json.dumps({
                "total": len(tasks),
                "active": active,
                "completed": completed,
                "archived": archived,
            }, separators=(",", ":")))
            return 0

        parser.error("a command is required")
    except (PersistenceError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return _run_command(args, parser)
