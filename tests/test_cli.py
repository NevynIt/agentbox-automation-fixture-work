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
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC)
        return subprocess.run(
            [sys.executable, "-m", "tinyboard", "--db", str(database), *arguments],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_add_and_list_use_required_output_and_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            added = self.run_cli(database, "add", "  Buy\tmilk  ")
            self.assertEqual(added.returncode, 0)
            self.assertEqual(added.stdout, "added 1\tBuy milk\n")

            second = self.run_cli(database, "add", "Call mum")
            self.assertEqual(second.stdout, "added 2\tCall mum\n")
            listed = self.run_cli(database, "list")
            self.assertEqual(listed.stdout, "1\t[ ]\tBuy milk\n2\t[ ]\tCall mum\n")

    def test_complete_persists_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            self.run_cli(database, "add", "Task")
            self.assertEqual(self.run_cli(database, "complete", "1").stdout, "completed 1\n")
            self.assertEqual(self.run_cli(database, "complete", "1").stdout, "completed 1\n")
            self.assertEqual(self.run_cli(database, "list").stdout, "1\t[x]\tTask\n")

    def test_duplicate_active_title_is_rejected_without_mutating_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            self.assertEqual(self.run_cli(database, "add", "  Buy\tmilk ").returncode, 0)
            before = database.read_bytes()

            duplicate = self.run_cli(database, "add", "buy  MILK")

            self.assertNotEqual(duplicate.returncode, 0)
            self.assertIn("active task already exists", duplicate.stderr)
            self.assertEqual(database.read_bytes(), before)
            records = json.loads(database.read_text())["tasks"]
            self.assertEqual(len(records), 1)

    def test_completed_title_can_be_added_again(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            self.assertEqual(self.run_cli(database, "add", "Buy milk").returncode, 0)
            self.assertEqual(self.run_cli(database, "complete", "1").returncode, 0)

            added = self.run_cli(database, "add", "buy\tmilk")

            self.assertEqual(added.returncode, 0)
            self.assertEqual(added.stdout, "added 2\tbuy milk\n")

    def test_unknown_id_fails_without_mutating_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            self.run_cli(database, "add", "Task")
            before = database.read_bytes()
            result = self.run_cli(database, "complete", "99")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(database.read_bytes(), before)

    def test_list_excludes_archived_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "board.json"
            database.write_text(json.dumps({
                "version": 1,
                "tasks": [
                    {"id": 2, "title": "visible", "completed": True, "archived": False},
                    {"id": 1, "title": "hidden", "completed": False, "archived": True},
                ],
            }))
            result = self.run_cli(database, "list")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "2\t[x]\tvisible\n")


if __name__ == "__main__":
    unittest.main()
