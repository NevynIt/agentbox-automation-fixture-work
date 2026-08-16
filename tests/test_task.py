from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tinyboard.task import Task, TaskIdAllocator, next_task_id, normalize_title


class TaskTests(unittest.TestCase):
    def test_new_task_normalizes_title_and_defaults_state(self) -> None:
        task = Task.new(1, "  Buy\t  milk ")

        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Buy milk")
        self.assertFalse(task.completed)
        self.assertFalse(task.archived)

    def test_direct_task_construction_normalizes_title(self) -> None:
        task = Task(1, "  Buy\t  milk ")

        self.assertEqual(task.title, "Buy milk")

    def test_direct_task_construction_rejects_empty_normalized_title(self) -> None:
        with self.assertRaises(ValueError):
            Task(1, " \t\n ")

    def test_title_normalization_rejects_empty_result(self) -> None:
        with self.assertRaises(ValueError):
            normalize_title(" \t\n ")

    def test_invalid_task_values_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Task.new(0, "task")
        with self.assertRaises(TypeError):
            normalize_title(None)  # type: ignore[arg-type]

    def test_ids_start_at_one_and_follow_maximum(self) -> None:
        self.assertEqual(next_task_id([]), 1)
        self.assertEqual(next_task_id([Task.new(2, "two"), 7]), 8)

    def test_allocator_does_not_reuse_gaps(self) -> None:
        allocator = TaskIdAllocator([1, 3])

        self.assertEqual(allocator.allocate(), 4)
        self.assertEqual(allocator.allocate(), 5)


if __name__ == "__main__":
    unittest.main()
