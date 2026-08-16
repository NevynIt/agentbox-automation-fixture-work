from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tinyboard.persistence import PersistenceError, load_tasks, save_tasks
from tinyboard.task import Task


class PersistenceTests(unittest.TestCase):
    def test_missing_file_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load_tasks(Path(directory) / "missing.json"), [])

    def test_round_trip_preserves_all_task_fields(self) -> None:
        tasks = [Task(4, "Buy milk", completed=True, archived=True)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.json"
            save_tasks(path, tasks)
            self.assertEqual(load_tasks(path), tasks)

    def test_saved_document_uses_schema_version_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.json"
            save_tasks(path, [])
            self.assertEqual(json.loads(path.read_text())['version'], 1)

    def test_missing_parent_directory_is_created(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "board.json"
            save_tasks(path, [])
            self.assertTrue(path.is_file())

    def test_malformed_json_is_rejected_without_overwriting_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.json"
            original = "{not json"
            path.write_text(original)
            with self.assertRaisesRegex(PersistenceError, "invalid JSON"):
                load_tasks(path)
            self.assertEqual(path.read_text(), original)

    def test_invalid_utf8_is_rejected_without_overwriting_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.json"
            original = b'{"version": 1, "tasks": [\xff]}'
            path.write_bytes(original)
            with self.assertRaisesRegex(PersistenceError, "invalid JSON encoding"):
                load_tasks(path)
            self.assertEqual(path.read_bytes(), original)

    def test_unsupported_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.json"
            path.write_text(json.dumps({"version": 2, "tasks": []}))
            with self.assertRaisesRegex(PersistenceError, "unsupported"):
                load_tasks(path)

    def test_replacement_uses_destination_directory_and_replace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.json"
            real_replace = __import__("os").replace
            with patch("tinyboard.persistence.os.replace", wraps=real_replace) as replace:
                save_tasks(path, [])
            temporary_path, destination = replace.call_args.args
            self.assertEqual(Path(destination), path)
            self.assertEqual(Path(temporary_path).parent, path.parent)


if __name__ == "__main__":
    unittest.main()
