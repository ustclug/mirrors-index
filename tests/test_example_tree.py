import tempfile
import unittest
from pathlib import Path

from tools.create_example_tree import (
    FILES,
    create_example_tree,
)


class CreateExampleTreeTests(unittest.TestCase):
    def test_creates_an_idempotent_example_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"

            self.assertEqual(create_example_tree(root), len(FILES))
            self.assertEqual(create_example_tree(root), len(FILES))

    def test_refuses_an_unmanaged_non_empty_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "real-data").mkdir()

            with self.assertRaises(RuntimeError):
                create_example_tree(root)


if __name__ == "__main__":
    unittest.main()
