from __future__ import annotations

import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class TinyBoardCliTests(unittest.TestCase):
    def run_cli(self, database: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SRC)
        return subprocess.run(
            [sys.executable, "-m", "tinyboard", "--db", str(database), *arguments],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_add_and_list_use_normalized_titles_and_exact_format(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            added = self.run_cli(database, "add", "  Buy\t  milk ")
            listed = self.run_cli(database, "list")

        self.assertEqual(added.returncode, 0)
        self.assertEqual(added.stdout, "added 1\tBuy milk\n")
        self.assertEqual(listed.returncode, 0)
        self.assertEqual(listed.stdout, "1\t[ ]\tBuy milk\n")
        self.assertEqual(listed.stderr, "")

    def test_complete_persists_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            self.assertEqual(self.run_cli(database, "add", "task").returncode, 0)
            first = self.run_cli(database, "complete", "1")
            second = self.run_cli(database, "complete", "1")
            listed = self.run_cli(database, "list")

        self.assertEqual(first.stdout, "completed 1\n")
        self.assertEqual(second.stdout, "completed 1\n")
        self.assertEqual(listed.stdout, "1\t[x]\ttask\n")

    def test_list_excludes_archived_tasks_and_sorts_numeric_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            database.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "tasks": [
                            {"id": 10, "title": "ten", "completed": False, "archived": False},
                            {"id": 2, "title": "two", "completed": True, "archived": False},
                            {"id": 1, "title": "old", "completed": False, "archived": True},
                        ],
                    }
                )
            )
            listed = self.run_cli(database, "list")

        self.assertEqual(listed.stdout, "2\t[x]\ttwo\n10\t[ ]\tten\n")

    def test_unknown_completion_does_not_mutate_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            self.assertEqual(self.run_cli(database, "add", "task").returncode, 0)
            before = database.read_bytes()
            result = self.run_cli(database, "complete", "99")
            after = database.read_bytes()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(after, before)

    def test_duplicate_active_title_is_rejected_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            self.assertEqual(self.run_cli(database, "add", "  Straße  ").returncode, 0)
            before = database.read_bytes()
            result = self.run_cli(database, "add", "STRASSE")
            after = database.read_bytes()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)
        self.assertEqual(after, before)

    def test_completed_title_can_be_added_again(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            self.assertEqual(self.run_cli(database, "add", "Buy milk").returncode, 0)
            self.assertEqual(self.run_cli(database, "complete", "1").returncode, 0)
            result = self.run_cli(database, "add", " buy   MILK ")
            listed = self.run_cli(database, "list")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(listed.stdout, "1\t[x]\tBuy milk\n2\t[ ]\tbuy MILK\n")


if __name__ == "__main__":
    unittest.main()
