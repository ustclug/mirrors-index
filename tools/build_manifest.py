import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
with open(DIST / "esbuild-meta.json") as source:
    metadata = json.load(source)

manifest = {}
for output, detail in metadata["outputs"].items():
    entrypoint = detail.get("entryPoint", "")
    if entrypoint.endswith("frontend/index.tsx"):
        manifest["index"] = "/" + str((ROOT / output).resolve().relative_to(DIST))
    elif entrypoint.endswith("frontend/status.tsx"):
        manifest["status"] = "/" + str((ROOT / output).resolve().relative_to(DIST))

if set(manifest) != {"index", "status"}:
    raise RuntimeError(f"Incomplete frontend manifest: {manifest}")

with open(DIST / "manifest.json", "w") as output:
    json.dump(manifest, output, indent=2, sort_keys=True)
    output.write("\n")

status_template = (ROOT / "status" / "status.html").read_text()
status_html = status_template.replace("{{ STATUS_SCRIPT }}", manifest["status"])
(DIST / "status" / "index.html").write_text(status_html)
