import json
import tempfile
import unittest
from pathlib import Path

from tools.create_example_tree import (
    FILES,
    MARKER,
    create_example_status,
    create_example_tree,
)


class CreateExampleTreeTests(unittest.TestCase):
    def test_creates_an_idempotent_example_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"

            self.assertEqual(create_example_tree(root), len(FILES))
            self.assertEqual(create_example_tree(root), len(FILES))
            self.assertTrue((root / MARKER).is_file())
            for relative_path in FILES:
                self.assertTrue((root / relative_path).is_file())
            self.assertTrue(
                (
                    root
                    / "debian-cd/current/arm64/iso-cd/debian-13.1.0-arm64-netinst.iso"
                ).is_file()
            )
            self.assertTrue(
                (root / "node/latest-v22.x/node-v22.18.0-arm64.msi").is_file()
            )
            status_path = Path(directory) / "dist/status/json"
            create_example_status(status_path)
            status = json.loads(status_path.read_text())
            self.assertEqual(
                [(item["name"], item["exitCode"], item["syncing"]) for item in status],
                [
                    ("debian", 0, False),
                    ("archlinux", 0, True),
                    ("ubuntu", 30, False),
                ],
            )

    def test_refuses_an_unmanaged_non_empty_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "real-data").mkdir()

            with self.assertRaises(RuntimeError):
                create_example_tree(root)


if __name__ == "__main__":
    unittest.main()
