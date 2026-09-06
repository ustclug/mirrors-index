import importlib
import sys
import unittest
from unittest import mock

import utils


class GenMirrorzTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (
            mock.patch.object(utils, "get_mirrorz_cname", return_value={}),
            mock.patch.object(utils, "get_resp_with_timeout", return_value=None),
        ):
            sys.modules.pop("genmirrorz", None)
            cls.genmirrorz = importlib.import_module("genmirrorz")

    def test_repository_description(self):
        mirrors = self.genmirrorz.parse_repo_with_meta(
            [("", "/help/aosp.html", "Help", "aosp")], []
        )

        self.assertEqual("Android 操作系统源代码", mirrors[0]["desc"])

    def test_cache_mapping_overrides_sync_status(self):
        repolist = [("", "", "", "pypi")]
        metas = [
            {
                "name": "pypi",
                "mirrorz": [{"name": "pypi"}],
                "nextRun": 10,
                "lastSuccess": 5,
                "syncing": False,
                "exitCode": 0,
                "size": 1,
                "upstream": "https://example.invalid",
            },
            {
                "name": "pypi",
                "mirrorz": [{"name": "pypi", "cache": True}],
                "nextRun": 10,
                "lastSuccess": 5,
                "syncing": False,
                "exitCode": 0,
                "size": 1,
                "upstream": "https://example.invalid",
            },
        ]

        mirrors = self.genmirrorz.parse_repo_with_meta(repolist, metas)

        self.assertEqual("C", mirrors[0]["status"])

    def test_cache_mapping_uses_logical_repository_name(self):
        metas = [
            {
                "name": "pypi-packages",
                "mirrorz": [{"name": "pypi", "cache": True}],
            }
        ]

        self.assertEqual({"pypi"}, self.genmirrorz.cached_repo_names(metas))

    def test_missing_repository_description_warns(self):
        with self.assertLogs("genmirrorz", level="WARNING") as logs:
            description = self.genmirrorz.repo_description("not-configured")

        self.assertEqual("", description)
        self.assertIn("missing MirrorZ description for not-configured", logs.output[0])

    def test_all_configured_descriptions_are_nonempty(self):
        self.assertTrue(self.genmirrorz.descriptions)
        self.assertTrue(all(self.genmirrorz.descriptions.values()))

    def test_missing_zfs_skips_repository_size(self):
        site = {}
        with (
            mock.patch.object(self.genmirrorz.shutil, "which", return_value=None),
            mock.patch.object(self.genmirrorz, "disk_info") as disk_info,
        ):
            self.genmirrorz.add_disk_info_if_available(site)

        disk_info.assert_not_called()
        self.assertNotIn("disk", site)


if __name__ == "__main__":
    unittest.main()
