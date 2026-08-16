from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tinyboard.domain import Task
from tinyboard.persistence import PersistenceError, load_tasks, save_tasks


class PersistenceTests(unittest.TestCase):
    def test_missing_file_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load_tasks(Path(directory) / "board.json"), [])

    def test_round_trip_and_schema(self) -> None:
        tasks = [Task(1, "Buy milk", True, True), Task(2, "Call mum")]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.json"
            save_tasks(path, tasks)
            self.assertEqual(load_tasks(path), tasks)
            self.assertEqual(json.loads(path.read_text())["version"], 1)

    def test_creates_missing_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "board.json"
            save_tasks(path, [])
            self.assertEqual(load_tasks(path), [])

    def test_rejects_malformed_and_does_not_replace_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.json"
            original = "{not json"
            path.write_text(original)
            with self.assertRaises(PersistenceError):
                load_tasks(path)
            self.assertEqual(path.read_text(), original)

    def test_rejects_unsupported_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.json"
            path.write_text(json.dumps({"version": 2, "tasks": []}))
            with self.assertRaisesRegex(PersistenceError, "unsupported"):
                load_tasks(path)


if __name__ == "__main__":
    unittest.main()
