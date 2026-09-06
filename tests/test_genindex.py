import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import genindex


class GenIndexTests(unittest.TestCase):
    def test_index_json_schema(self):
        encoded = genindex.index_json(
            [("2026-01-02 03:04:05", "/help/debian.html", "Help", "debian")],
            [("source.example", "proxy.example")],
            [{"distro": "</script><img>", "category": "os", "urls": []}],
            [SimpleNamespace(title="News & more", link="https://example.com/news")],
            "2026-01-02 03:04:05",
        )
        data = json.loads(encoded)
        self.assertEqual(data["schemaVersion"], 1)
        self.assertEqual(data["repositories"][0]["name"], "debian")
        self.assertEqual(
            data["repositories"][0]["desc"],
            "Debian Linux 的官方软件包仓库",
        )
        self.assertEqual(data["reverseProxies"][0]["destination"], "proxy.example")

    def run_generator(self, directory, mirrorz_generator):
        fake_mirrorz = SimpleNamespace(getMirrorzJson=mirrorz_generator)
        repolist = [("2026-01-02 03:04:05", "/help/debian.html", "Help", "debian")]
        with (
            mock.patch.object(
                genindex.gencontent, "genRepoList", return_value=repolist
            ),
            mock.patch.object(
                genindex.gencontent,
                "getOthers",
                return_value=[("source.example", "proxy.example")],
            ),
            mock.patch.object(genindex, "get_isolist", return_value=[]),
            mock.patch.object(genindex.genservernews, "getServerNews", return_value=[]),
            mock.patch.dict("sys.modules", {"genmirrorz": fake_mirrorz}),
            mock.patch("sys.argv", ["genindex.py", "--outdir", directory]),
        ):
            genindex.main()

    def test_directory_generation_does_not_touch_index_html(self):
        with tempfile.TemporaryDirectory() as directory:
            index_html = os.path.join(directory, "index.html")
            with open(index_html, "w") as output:
                output.write("deployed homepage")

            self.run_generator(directory, lambda _repos, _downloads: '{"site":{}}')

            with open(index_html) as source:
                self.assertEqual(source.read(), "deployed homepage")
            with open(
                os.path.join(directory, "static", "json", "index.json")
            ) as source:
                self.assertEqual(json.load(source)["repositories"][0]["name"], "debian")
            self.assertTrue(os.path.exists(os.path.join(directory, "index-nojs.html")))
            with open(
                os.path.join(directory, "static", "json", "mirrorz.json")
            ) as source:
                self.assertEqual(json.load(source), {"site": {}})

    def test_mirrorz_failure_keeps_old_file_and_publishes_other_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            mirrorz_path = os.path.join(directory, "static", "json", "mirrorz.json")
            os.makedirs(os.path.dirname(mirrorz_path), exist_ok=True)
            with open(mirrorz_path, "w") as output:
                output.write("old mirrorz")

            def fail_mirrorz(_repos, _downloads):
                raise RuntimeError("mirrorz unavailable")

            with self.assertRaises(SystemExit) as raised:
                self.run_generator(directory, fail_mirrorz)

            self.assertEqual(raised.exception.code, 1)
            with open(mirrorz_path) as source:
                self.assertEqual(source.read(), "old mirrorz")
            self.assertTrue(
                os.path.exists(os.path.join(directory, "static", "json", "index.json"))
            )
            self.assertTrue(os.path.exists(os.path.join(directory, "index-nojs.html")))

    def test_atomic_write_replaces_complete_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "index.html")
            with open(target, "w") as output:
                output.write("old")
            genindex.atomic_write(target, "new")
            with open(target) as output:
                self.assertEqual(output.read(), "new" + os.linesep)
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o644)


if __name__ == "__main__":
    unittest.main()
