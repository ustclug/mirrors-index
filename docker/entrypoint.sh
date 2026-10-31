#!/bin/sh
set -eu
outdir="${OUTDIR:-/output}"
test -f "${CONFIG_DIR:-/config}/site.json"
mkdir -p "$outdir"
exec 9>"$outdir/.mirrors-index.lock"
flock -n 9
# HTML is rendered by genindex; never overwrite an existing site's pages here.
rsync -a --no-owner --no-group --exclude='*.html' --exclude=/manifest.json --exclude=/esbuild-meta.json /app/dist/ "$outdir/"
exec python3 /app/genindex.py --outdir "$outdir" --assets-dir /app/dist "$@"
