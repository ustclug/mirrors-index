import json
import os
import tempfile
import unittest
from types import SimpleNamespace

import genindex


class GenIndexTests(unittest.TestCase):
    def test_bootstrap_schema_and_script_escaping(self):
        encoded = genindex.bootstrap_json(
            [("2026-01-02 03:04:05", "/help/debian.html", "Help", "debian")],
            [("source.example", "proxy.example")],
            [{"distro": "</script><img>", "category": "os", "urls": []}],
            [SimpleNamespace(title="News & more", link="https://example.com/news")],
            "2026-01-02 03:04:05",
        )
        self.assertNotIn("</script>", encoded)
        data = json.loads(encoded)
        self.assertEqual(data["schemaVersion"], 1)
        self.assertEqual(data["repositories"][0]["name"], "debian")
        self.assertEqual(data["reverseProxies"][0]["destination"], "proxy.example")

    def test_atomic_write_replaces_complete_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "index.html")
            with open(target, "w") as output:
                output.write("old")
            genindex.atomic_write(target, "new")
            with open(target) as output:
                self.assertEqual(output.read(), "new" + os.linesep)
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o644)

    def test_frontend_manifest_rejects_non_static_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, "dist"))
            with open(os.path.join(directory, "dist", "manifest.json"), "w") as output:
                json.dump({"index": "https://example.com/script.js"}, output)
            with self.assertRaises(RuntimeError):
                genindex.frontend_asset("index", directory)


if __name__ == "__main__":
    unittest.main()
