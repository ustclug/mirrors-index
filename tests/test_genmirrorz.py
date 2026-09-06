import importlib
import io
import json
import sys
import unittest
from contextlib import redirect_stderr
from unittest import mock

import utils

DEFAULT_MAPPING = object()


def make_meta(name="task", mirrorz=DEFAULT_MAPPING, **overrides):
    meta = {
        "name": name,
        "nextRun": 100,
        "lastSuccess": 50,
        "prevRun": 40,
        "syncing": False,
        "exitCode": 0,
        "size": 1024,
        "upstream": "https://example.invalid",
        "disable": False,
    }
    if mirrorz is not DEFAULT_MAPPING:
        meta["mirrorz"] = mirrorz
    meta.update(overrides)
    return meta


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

    def test_repository_description_is_case_insensitive(self):
        self.assertEqual("Perl 语言软件库", self.genmirrorz.repo_description("CPAN"))

    def test_canonical_name_collision_keeps_last_repository(self):
        with mock.patch.object(
            self.genmirrorz,
            "cname",
            {"archive.raspberrypi.org": "raspberrypi"},
        ):
            mirrors = self.genmirrorz.parse_repo_with_meta(
                [
                    ("", "/help/archive.html", "", "archive.raspberrypi.org"),
                    ("", "/help/raspberrypi.html", "", "raspberrypi"),
                ],
                [make_meta("raspberrypi", syncing=True)],
            )

        self.assertEqual(1, len(mirrors))
        self.assertEqual("raspberrypi", mirrors[0]["cname"])
        self.assertEqual("/raspberrypi", mirrors[0]["url"])
        self.assertEqual("/help/raspberrypi.html", mirrors[0]["help"])
        self.assertEqual("Y40O50X100", mirrors[0]["status"])

    def test_cache_mapping_overrides_sync_status(self):
        repolist = [("", "", "", "pypi")]
        metas = [
            make_meta("pypi", [{"name": "pypi"}]),
            make_meta(
                "pypi-cache",
                [{"name": "pypi", "cache": True}],
                disable=True,
            ),
        ]

        mirrors = self.genmirrorz.parse_repo_with_meta(repolist, metas)

        self.assertEqual("C", mirrors[0]["status"])

    def test_mapping_defaults_excludes_and_maps_multiple_repositories(self):
        grouped = self.genmirrorz.collect_repo_contributions(
            [
                make_meta("default"),
                make_meta("excluded", []),
                make_meta("split", [{"name": "one"}, {"name": "two"}]),
            ]
        )

        self.assertEqual({"default", "one", "two"}, set(grouped))

    def test_task_metadata_uses_logical_repository_mapping(self):
        meta = make_meta(
            "anaconda-conda-forge-cache",
            [{"name": "anaconda", "cache": True}],
        )
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            mirrors = self.genmirrorz.parse_repo_with_meta(
                [("", "", "", "anaconda")], [meta]
            )

        self.assertEqual("C", mirrors[0]["status"])
        self.assertEqual("0.00 MiB", mirrors[0]["size"])
        self.assertEqual("https://example.invalid", mirrors[0]["upstream"])
        self.assertEqual("", stderr.getvalue())

    def test_empty_mapping_excludes_task_metadata(self):
        meta = make_meta("internal-index", [])
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            mirrors = self.genmirrorz.parse_repo_with_meta(
                [("", "", "", "aosp")], [meta]
            )

        self.assertEqual("U", mirrors[0]["status"])
        self.assertNotIn("size", mirrors[0])
        self.assertEqual("", stderr.getvalue())

    def test_status_aggregation_is_conservative_and_order_independent(self):
        contributions = [
            self.genmirrorz.RepoContribution(
                "failed", False, False, False, 10, 70, 90, 200, 100, "one"
            ),
            self.genmirrorz.RepoContribution(
                "syncing", False, False, True, 10, 60, 40, 150, 200, "two"
            ),
            self.genmirrorz.RepoContribution(
                "success", False, False, False, 0, 50, 30, 120, 300, "three"
            ),
        ]

        self.assertEqual("F90O50X120", self.genmirrorz.aggregate_status(contributions))
        self.assertEqual(
            self.genmirrorz.aggregate_status(contributions),
            self.genmirrorz.aggregate_status(list(reversed(contributions))),
        )
        self.assertEqual(
            "Y40O50X120",
            self.genmirrorz.aggregate_status(contributions[1:]),
        )

    def test_disabled_tasks_are_excluded_from_status_but_keep_metadata(self):
        active = self.genmirrorz.RepoContribution(
            "active", False, False, False, 0, 100, 90, 200, 1024, "active"
        )
        disabled = self.genmirrorz.RepoContribution(
            "disabled", False, True, False, 10, 10, 20, -1, 2097152, "disabled"
        )

        aggregate = self.genmirrorz.aggregate_contributions([active, disabled])

        self.assertEqual("S100X200", aggregate["status"])
        self.assertEqual("2.00 MiB", aggregate["size"])
        self.assertEqual("", aggregate["upstream"])
        self.assertEqual("P", self.genmirrorz.aggregate_status([disabled]))

    def test_size_uses_maximum_and_identical_upstream_is_preserved(self):
        contributions = [
            self.genmirrorz.RepoContribution(
                "one", False, False, False, 0, 10, 5, 20, 1024, "same"
            ),
            self.genmirrorz.RepoContribution(
                "two", False, False, False, 0, 20, 15, 30, 2097152, "same"
            ),
        ]

        aggregate = self.genmirrorz.aggregate_contributions(contributions)

        self.assertEqual("2.00 MiB", aggregate["size"])
        self.assertEqual("same", aggregate["upstream"])
        self.assertEqual("S10X20", aggregate["status"])

    def test_skiplist_applies_before_cache_aggregation(self):
        with mock.patch.object(self.genmirrorz, "skiplist", ["cache-task"]):
            grouped = self.genmirrorz.collect_repo_contributions(
                [
                    make_meta(
                        "cache-task",
                        [{"name": "pypi", "cache": True}],
                    )
                ]
            )

        self.assertEqual({}, grouped)

    def test_skiplist_removes_repository_from_mirrorz_output(self):
        with mock.patch.object(self.genmirrorz, "skiplist", ["misc", "ustclug"]):
            mirrors = self.genmirrorz.parse_repo_with_meta(
                [
                    ("", "", "", "aosp"),
                    ("", "", "", "misc"),
                    ("", "", "", "ustclug"),
                ],
                [
                    make_meta("misc"),
                    make_meta("internal", [{"name": "ustclug"}]),
                ],
            )

        self.assertEqual(["aosp"], [mirror["cname"] for mirror in mirrors])

    def test_unpublished_mapping_warns_once_for_all_tasks(self):
        metas = [
            make_meta("one", [{"name": "missing"}]),
            make_meta("two", [{"name": "missing"}]),
        ]

        with self.assertLogs("genmirrorz", level="WARNING") as logs:
            self.genmirrorz.parse_repo_with_meta([("", "", "", "aosp")], metas)

        matching = [line for line in logs.output if "unpublished" in line]
        self.assertEqual(1, len(matching))
        self.assertIn("one, two", matching[0])

    def test_invalid_task_does_not_block_valid_metadata(self):
        with self.assertLogs("genmirrorz", level="WARNING"):
            grouped = self.genmirrorz.collect_repo_contributions(
                [
                    {"name": "invalid"},
                    make_meta("wrong-type", nextRun="tomorrow"),
                    make_meta("valid"),
                ]
            )

        self.assertEqual({"valid"}, set(grouped))

    def test_fetch_yuki_metas_keeps_successful_endpoints(self):
        response = mock.Mock()
        response.json.return_value = [make_meta("valid")]
        config = {
            "yuki": [
                {"url": "https://disabled.invalid", "mirrorz": False},
                {"url": "https://failed.invalid", "mirrorz": True},
                {"url": "https://valid.invalid", "mirrorz": True},
            ]
        }

        with (
            mock.patch.object(self.genmirrorz, "gencontent_config", config),
            mock.patch.object(
                self.genmirrorz,
                "get_resp_with_timeout",
                side_effect=[None, response],
            ) as get_response,
            self.assertLogs("genmirrorz", level="ERROR"),
        ):
            metas = self.genmirrorz.fetch_yuki_metas()

        self.assertEqual([make_meta("valid")], metas)
        self.assertEqual(2, get_response.call_count)

    def test_get_mirrorz_json_fetches_metadata_without_mutating_base(self):
        original_base = json.loads(json.dumps(self.genmirrorz.base))
        with (
            mock.patch.object(
                self.genmirrorz,
                "fetch_yuki_metas",
                return_value=[make_meta("aosp")],
            ) as fetch,
            mock.patch.object(self.genmirrorz, "add_disk_info_if_available"),
        ):
            result = json.loads(
                self.genmirrorz.getMirrorzJson([("", "", "", "aosp")], [])
            )

        fetch.assert_called_once_with()
        self.assertEqual("S50X100", result["mirrors"][0]["status"])
        self.assertEqual(original_base, self.genmirrorz.base)

    def test_cname_is_applied_before_grouping(self):
        with mock.patch.object(
            self.genmirrorz,
            "cname",
            {"debian-multimedia": "deb-multimedia"},
        ):
            grouped = self.genmirrorz.collect_repo_contributions(
                [make_meta("debian-multimedia")]
            )

        self.assertEqual({"deb-multimedia"}, set(grouped))

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
