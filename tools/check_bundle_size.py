import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
with open(ROOT / "dist" / "manifest.json") as source:
    manifest = json.load(source)

limit = 20 * 1024
for name, url in manifest.items():
    path = ROOT / "dist" / url.removeprefix("/")
    size = len(gzip.compress(path.read_bytes(), compresslevel=9))
    print(f"{name}: {size} bytes gzip")
    if size > limit:
        raise RuntimeError(f"{name} exceeds the {limit}-byte gzip budget")
