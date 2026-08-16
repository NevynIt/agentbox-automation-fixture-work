from __future__ import annotations

import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tinyboard.domain import InvalidTitleError, Task, allocate_id, normalize_title


class TaskDomainTests(unittest.TestCase):
    def test_normalizes_outer_and_internal_whitespace(self) -> None:
        self.assertEqual(normalize_title("  Buy\t\nmilk "), "Buy milk")

    def test_rejects_empty_normalized_title(self) -> None:
        with self.assertRaises(InvalidTitleError):
            Task.create(1, " \t\n ")

    def test_new_task_defaults(self) -> None:
        task = Task.create(1, "New task")
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "New task")
        self.assertFalse(task.completed)
        self.assertFalse(task.archived)

    def test_first_id_is_one(self) -> None:
        self.assertEqual(allocate_id([]), 1)

    def test_allocates_after_maximum_without_reusing_gaps(self) -> None:
        tasks = [Task.create(1, "one"), Task.create(4, "four")]
        self.assertEqual(allocate_id(tasks), 5)


if __name__ == "__main__":
    unittest.main()
