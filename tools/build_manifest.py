import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
with open(DIST / "esbuild-meta.json") as source:
    metadata = json.load(source)

entries = {
    "frontend/index.tsx": "index",
    "frontend/status.tsx": "status",
    "static/css/style.css": "index_style",
    "static/css/status.css": "status_style",
}
manifest = {}
for output, detail in metadata["outputs"].items():
    entrypoint = detail.get("entryPoint", "")
    for suffix, name in entries.items():
        if entrypoint.endswith(suffix):
            manifest[name] = "/" + str((ROOT / output).resolve().relative_to(DIST))

if set(manifest) != set(entries.values()):
    raise RuntimeError(f"Incomplete frontend manifest: {manifest}")

with open(DIST / "manifest.json", "w") as output:
    json.dump(manifest, output, indent=2, sort_keys=True)
    output.write("\n")

environment = Environment(
    loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"])
)
index_html = environment.get_template("index.html").render(
    index_script=manifest["index"], index_style=manifest["index_style"]
)
(DIST / "index.html").write_text(index_html + "\n")

status_template = (ROOT / "status" / "status.html").read_text()
status_html = status_template.replace("{{ STATUS_SCRIPT }}", manifest["status"])
status_html = status_html.replace("{{ STATUS_STYLE }}", manifest["status_style"])
(DIST / "status" / "index.html").write_text(status_html)
