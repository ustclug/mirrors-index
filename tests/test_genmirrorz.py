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
