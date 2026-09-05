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
        "urls": [{"name": "1.0 (amd64)", "url": "/test-os.iso"}],
    },
    {
        "distro": "Test App",
        "category": "app",
        "urls": [{"name": "2.0", "url": "/test-app.zip"}],
    },
]
news = [SimpleNamespace(title="Test news", link="https://example.com/news")]
env = Environment(
    loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"])
)
html = env.get_template("index.html").render(
    repolist=repolist,
    bootstrap=genindex.bootstrap_json(
        repolist, [("source", "destination")], downloads, news, "2026-01-02 03:04:05"
    ),
    index_script=genindex.frontend_asset("index", ROOT),
    now="2026-01-02 03:04:05",
)
(ROOT / "dist" / "index.html").write_text(html + "\n")
(ROOT / "dist" / "index-nojs.html").write_text(
    env.get_template("index-nojs.html").render(
        repolist=repolist, now="2026-01-02 03:04:05"
    )
    + "\n"
)
(ROOT / "dist" / "invalid.html").write_text(
    html.replace('"schemaVersion":1', '"schemaVersion":2') + "\n"
)
