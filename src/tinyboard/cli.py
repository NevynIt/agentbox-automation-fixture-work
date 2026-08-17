"""TinyBoard command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .storage import Board, StorageError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tinyboard")
    parser.add_argument(
        "--version",
        action="version",
        version=f"tinyboard {__version__}",
    )
    parser.add_argument("--db", type=Path, default=Path(".tinyboard.json"))
    commands = parser.add_subparsers(dest="command")
    add = commands.add_parser("add")
    add.add_argument("title")
    commands.add_parser("list")
    complete = commands.add_parser("complete")
    complete.add_argument("id", type=int)
    commands.add_parser("summary")
    archive = commands.add_parser("archive")
    archive.add_argument("id", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        return 0
    try:
        board = Board.load(args.db)
        if args.command == "add":
            task = board.add(args.title)
            print(f"added {task.id}\t{task.title}")
        elif args.command == "list":
            for task in sorted((item for item in board.tasks if not item.archived), key=lambda item: item.id):
                print(f"{task.id}\t{'[x]' if task.completed else '[ ]'}\t{task.title}")
        elif args.command == "complete":
            task = next((item for item in board.tasks if item.id == args.id), None)
            if task is None:
                raise ValueError(f"unknown task {args.id}")
            task.completed = True
            board.save()
            print(f"completed {task.id}")
        elif args.command == "archive":
            task = next((item for item in board.tasks if item.id == args.id), None)
            if task is None or not task.completed:
                raise ValueError("only a completed task may be archived")
            task.archived = True
            board.save()
            print(f"archived {task.id}")
        elif args.command == "summary":
            print(json.dumps({"total": len(board.tasks), "active": sum(item.active for item in board.tasks),
                              "completed": sum(item.completed for item in board.tasks),
                              "archived": sum(item.archived for item in board.tasks)}))
    except (StorageError, ValueError) as exc:
        parser.error(str(exc))
    return 0
