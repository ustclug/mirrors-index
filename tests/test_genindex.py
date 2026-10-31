import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import genindex
import siteconfig


class GenIndexTests(unittest.TestCase):
    def run_generator(
        self, directory, mirrorz_generator, httpdir_exists=True, assets_dir=None
    ):
        fake_mirrorz = SimpleNamespace(
            collect_repo_contributions=mock.Mock(),
            getMirrorzJson=lambda repos, downloads, meta=None: mirrorz_generator(
                repos, downloads
            ),
        )
        repolist = [("2026-01-02 03:04:05", "/help/debian.html", "Help", "debian")]
        metadata = [
            {
                "name": "debian",
                "mirrorz": [{"name": "debian"}],
                "lastSuccess": 1,
            }
        ]
        snapshots = [
            ({"homepage": True, "mirrorz": True}, metadata),
        ]
        with (
            mock.patch.object(
                genindex.gencontent, "fetch_yuki_metadata", return_value=snapshots
            ),
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
            mock.patch.object(genindex, "httpdir_exists", return_value=httpdir_exists),
            mock.patch.dict("sys.modules", {"genmirrorz": fake_mirrorz}),
            mock.patch(
                "sys.argv",
                ["genindex.py", "--outdir", directory]
                + (["--assets-dir", assets_dir] if assets_dir else []),
            ),
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

    def test_missing_httpdir_warns_and_generation_continues(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertLogs("mirrors-genindex", level="WARNING") as logs:
                self.run_generator(
                    directory,
                    lambda _repos, _downloads: '{"site":{}}',
                    httpdir_exists=False,
                )

            self.assertTrue(
                os.path.exists(os.path.join(directory, "static", "json", "index.json"))
            )
            self.assertTrue(
                any("HTTPDIR" in message for message in logs.output), logs.output
            )

    def test_yuki_failure_keeps_all_old_files(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [
                os.path.join(directory, "static", "json", "index.json"),
                os.path.join(directory, "index-nojs.html"),
                os.path.join(directory, "static", "json", "mirrorz.json"),
            ]
            for path in paths:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as output:
                    output.write("old")

            with (
                mock.patch.object(
                    genindex.gencontent,
                    "fetch_yuki_metadata",
                    side_effect=genindex.gencontent.YukiMetadataError("unavailable"),
                ),
                mock.patch(
                    "sys.argv",
                    ["genindex.py", "--outdir", directory],
                ),
                self.assertRaises(genindex.gencontent.YukiMetadataError),
            ):
                genindex.main()

            for path in paths:
                with open(path) as source:
                    self.assertEqual("old", source.read())

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

    def test_site_templates_escape_markup_and_exclude_private_config(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "manifest.json").write_text(
                json.dumps(
                    {
                        "index": "/app.js",
                        "index_style": "/app.css",
                        "status": "/status.js",
                        "status_style": "/status.css",
                    }
                )
            )
            with mock.patch.object(
                siteconfig,
                "SITE",
                {
                    "name": "</script><img src=x>",
                    "abbr": "EX",
                    "url": "https://example.org",
                    "newsFeed": "https://private.example/feed",
                },
            ):
                pages = genindex.site_pages(directory)
            for name in ("index.html", "status/index.html"):
                with self.subTest(page=name):
                    self.assertNotIn("</script><img", pages[name])
                    self.assertIn("&lt;/script&gt;&lt;img src=x&gt;", pages[name])
                    self.assertNotIn("private.example", pages[name])
                    payload = (
                        pages[name]
                        .split('id="site-config">', 1)[1]
                        .split("</script>", 1)[0]
                    )
                    self.assertEqual(
                        json.loads(payload)["name"], "</script><img src=x>"
                    )
            self.assertNotIn("private.example", pages["static/json/site.json"])

    def test_full_generation_failure_keeps_pages_and_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [
                "index.html",
                "index-nojs.html",
                "status/index.html",
                "static/json/index.json",
                "static/json/mirrorz.json",
                "static/json/site.json",
            ]
            for path in paths:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("old")

            def fail(_repos, _downloads):
                raise ValueError("invalid MirrorZ data")

            with (
                mock.patch.object(
                    genindex, "site_pages", return_value={"index.html": "new"}
                ),
                self.assertRaisesRegex(ValueError, "invalid MirrorZ"),
            ):
                self.run_generator(directory, fail, assets_dir="unused")
            for path in paths:
                with self.subTest(path=path):
                    self.assertEqual((root / path).read_text(), "old")


if __name__ == "__main__":
    unittest.main()
