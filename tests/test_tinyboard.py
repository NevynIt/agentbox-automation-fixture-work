from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TinyBoardTests(unittest.TestCase):
    def run_cli(self, db: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run([sys.executable, "-m", "tinyboard", "--db", str(db), *args],
                              cwd=ROOT, env=env, text=True, capture_output=True)

    def test_complete_archive_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "board.json"
            self.assertEqual(self.run_cli(db, "add", "  Buy   milk ").stdout, "added 1\tBuy milk\n")
            self.assertEqual(self.run_cli(db, "complete", "1").returncode, 0)
            self.assertEqual(self.run_cli(db, "archive", "1").returncode, 0)
            summary = json.loads(self.run_cli(db, "summary").stdout)
            self.assertEqual(summary, {"total": 1, "active": 0, "completed": 1, "archived": 1})

    def test_duplicate_active_title_and_completed_readd(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "board.json"
            self.assertEqual(self.run_cli(db, "add", "Buy milk").returncode, 0)
            self.assertNotEqual(self.run_cli(db, "add", " buy   MILK ").returncode, 0)
            self.assertEqual(self.run_cli(db, "complete", "1").returncode, 0)
            self.assertEqual(self.run_cli(db, "add", "buy milk").returncode, 0)

    def test_malformed_database_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "board.json"
            db.write_text("{broken", encoding="utf-8")
            result = self.run_cli(db, "list")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(db.read_text(encoding="utf-8"), "{broken")
