import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import gencontent


def make_task(name="repo", mirrorz=None, last_success=100):
    task = {"name": name, "lastSuccess": last_success}
    if mirrorz is not None:
        task["mirrorz"] = mirrorz
    return task


class GenContentTests(unittest.TestCase):
    def repositories(self, metadata, manual=None):
        with (
            mock.patch.object(gencontent, "MANUAL_REPOSITORIES", manual or []),
            mock.patch.object(gencontent, "get_help_link", return_value=""),
        ):
            return list(gencontent.generate_repo_list(metadata))

    def test_repository_list_uses_mappings_and_latest_success(self):
        metadata = [
            make_task("one", [{"name": "shared"}], 100),
            make_task("two", [{"name": "shared"}], 200),
            make_task("default", last_success=150),
            make_task("excluded", [], 300),
        ]

        repositories = self.repositories(metadata)

        self.assertEqual(["default", "shared"], [item[3] for item in repositories])
        self.assertEqual(
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(200)),
            repositories[1][0],
        )

    def test_manual_repositories_are_merged_with_blank_update_time(self):
        repositories = self.repositories(
            [make_task("from-yuki", last_success=100)],
            ["manual", "from-yuki"],
        )

        self.assertEqual(["from-yuki", "manual"], [item[3] for item in repositories])
        self.assertNotEqual("", repositories[0][0])
        self.assertEqual("", repositories[1][0])

    def test_repository_names_are_case_sensitive(self):
        repositories = self.repositories(
            [make_task("task", [{"name": "CPAN"}], 100)], ["cpan"]
        )

        self.assertEqual(["CPAN", "cpan"], [item[3] for item in repositories])

    def test_legacy_empty_mapping_object_excludes_task(self):
        self.assertEqual([], self.repositories([make_task("excluded", {})]))

    def test_nonempty_mapping_object_is_rejected(self):
        with self.assertRaisesRegex(gencontent.YukiMetadataError, "must be a list"):
            self.repositories([make_task("invalid", {"name": "invalid"})])

    def test_invalid_last_success_is_rejected(self):
        with self.assertRaisesRegex(gencontent.YukiMetadataError, "lastSuccess"):
            self.repositories([make_task(last_success=True)])

    def test_help_link_is_read_from_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            helpdir = Path(directory) / "help"
            helpdir.mkdir()
            (helpdir / "repo.html").write_text("help")
            with mock.patch.object(gencontent, "HELPDIR", None):
                self.assertEqual(
                    "/help/repo.html", gencontent.get_help_link("repo", directory)
                )
                self.assertEqual("", gencontent.get_help_link("missing", directory))

    def test_help_link_uses_configured_local_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            helpdir = Path(directory) / "custom-help"
            helpdir.mkdir()
            (helpdir / "repo.html").write_text("help")
            with mock.patch.object(gencontent, "HELPDIR", str(helpdir)):
                self.assertEqual(
                    "/help/repo.html",
                    gencontent.get_help_link("repo", "/unused/output"),
                )


if __name__ == "__main__":
    unittest.main()
