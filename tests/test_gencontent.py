import time
import unittest
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
            mock.patch.object(gencontent, "testHelpLink", return_value=""),
        ):
            return list(gencontent.genRepoList(metadata))

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

    def test_fetch_yuki_metadata_is_strict(self):
        valid_response = mock.Mock()
        valid_response.json.return_value = [make_task()]
        config = {
            "yuki": [
                {
                    "url": "https://valid.invalid",
                    "homepage": True,
                    "mirrorz": True,
                }
            ]
        }
        with (
            mock.patch.object(gencontent, "USER_CONFIG", config),
            mock.patch.object(
                gencontent.utils,
                "get_resp_with_timeout",
                return_value=valid_response,
            ) as get_response,
        ):
            snapshots = gencontent.fetch_yuki_metadata()

        self.assertEqual([(config["yuki"][0], [make_task()])], snapshots)
        get_response.assert_called_once_with(
            "https://valid.invalid", logger=gencontent.logger
        )

        with (
            mock.patch.object(gencontent, "USER_CONFIG", config),
            mock.patch.object(
                gencontent.utils, "get_resp_with_timeout", return_value=None
            ),
            self.assertRaisesRegex(gencontent.YukiMetadataError, "failed to get"),
        ):
            gencontent.fetch_yuki_metadata()


if __name__ == "__main__":
    unittest.main()
