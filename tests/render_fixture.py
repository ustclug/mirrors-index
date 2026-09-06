import sys
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import genindex

repolist = [
    ("2026-01-02 03:04:05", "/help/alpha.html", "Help", "alpha"),
    ("2026-01-03 04:05:06", "", "", "beta"),
]
downloads = [
    {
        "distro": "Test OS",
        "category": "os",
        "urls": [
            {"name": "1.0 (amd64)", "url": "/test-os.iso"},
            {"name": "1.0 (arm64)", "url": "/test-os-arm64.iso"},
        ],
    },
    {
        "distro": "Test App",
        "category": "app",
        "urls": [{"name": "2.0", "url": "/test-app.zip"}],
    },
]
news = [SimpleNamespace(title="Test news", link="https://example.com/news")]
genindex.descriptions["alpha"] = "Alpha repository description"
env = Environment(
    loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"])
)
(ROOT / "dist" / "static" / "index.json").write_text(
    genindex.index_json(
        repolist, [("source", "destination")], downloads, news, "2026-01-02 03:04:05"
    )
    + "\n"
)
(ROOT / "dist" / "index-nojs.html").write_text(
    env.get_template("index-nojs.html").render(
        repolist=repolist,
        descriptions=genindex.descriptions,
        now="2026-01-02 03:04:05",
    )
    + "\n"
)
