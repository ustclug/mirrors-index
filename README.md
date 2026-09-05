# mirrors-index

Help documentation source code: https://github.com/ustclug/mirrorhelp/

## Dependencies

* python3
* python3-requests
* python3-jinja2
* nodejs (>= 20, only required while deploying or developing)
* esbuild
* typescript
* systemd

## Install

genisolist is a submodule of mirrorz-genisolist, so please checkout the submodule first:

```shell
git submodule update --init --recursive
```

Assuming that your metadata is stored in `/srv/repo`. Otherwise, you should modify the `HTTPDIR` variable in gencontent.py (by gencontent.json), and root attribute in genisolist.ini.

Metadata now is generated from rsync-huai hook after every sync by yuki.

### Build and deploy

The browser application uses the audited Preact copy under `vendor/`, while
repository discovery and page data generation remain in Python. Production
does not need npm or pnpm. Build on the production machine and install the
static application into the web root:

```shell
make build
python3 genindex.py --outdir /srv/www/
make install WEBROOT=/srv/www
```

`make install` installs the already-built static homepage, hashed JavaScript and
CSS bundles, fonts, and `/status/` page. It does not rebuild them. The periodic
job only needs Python; build tools and Node package managers are not involved in
hourly updates. The `mirror` user running the periodic job must be able to create
and replace files in `/srv/www/` and `/srv/www/static/`. See
`vendor/preact/VENDORING.md` for the vendored source and update procedure.

The generated homepage links browsers without JavaScript or ES module support
to a separate `index-nojs.html` containing the repository list. The full
interface fetches versioned data from `/static/index.json`. The periodic job
atomically updates that file, `index-nojs.html`, and `mirrorz.json`; it never
modifies `index.html`.

### Periodic updates

Install the service and timer, then enable the timer:

```shell
install -m 0644 services/mirrors-index.service services/mirrors-index.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now mirrors-index.timer
```

The timer regenerates the homepage data files every hour at minute 10. Run an
initial generation immediately after deployment with:

```shell
systemctl start mirrors-index.service
```

### Locales

Install zh_CN locales since the `genisolist.ini` file contains Chinese characters.

## Development

Here we introduce how to develop this project on your personal computer (without polluting host's filesystem environment).

Build the development image:

```shell
docker build -t mirrors-index-dev .
```

The Debian 13-based image contains Node.js 22, the Python dependencies, pinned
frontend tools, Chromium, and the Playwright development dependency. It runs as
the non-root `node` user (UID 1000). Start a shell using the source tree included
in the image:

```shell
docker run --rm -it -p 8000:8000 mirrors-index-dev
```

For live editing, bind mount the checkout and keep `node_modules` in a named
volume. Run `pnpm install` once after creating or replacing that volume:

```shell
docker run --rm -it -p 8000:8000 \
    -v "$PWD:/workspace" \
    -v mirrors-index-node-modules:/workspace/node_modules \
    mirrors-index-dev
pnpm install --frozen-lockfile --ignore-scripts
```

The image provides a writable `/srv/repo` directory for fake metadata. Run
`make example` to populate it with a small representative repository tree. The
generator is idempotent and refuses to touch a non-empty directory it did not
create. It also writes example sync data to `dist/status/json`, so the
status page works with the same local server. A different destination can be
passed directly, for example:

```shell
python3 tools/create_example_tree.py /tmp/example-repo
```

Run
`python3 -m http.server --directory /srv/repo 8000` to serve it on the exposed
port when needed.

Use these entry points during development:

```shell
make build       # type-check and create production assets under dist/
make dev         # watch the TypeScript entry points
make format      # format project-owned Python files with Ruff
make lint        # check Ruff formatting and lint rules
make test        # Python unit tests and Playwright browser tests
python3 genindex.py --outdir dist/
python3 -m http.server --directory dist
```

Playwright uses `/usr/bin/chromium` by default. Set
`PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` when Chromium is installed elsewhere.

If you need to debug genisolist, use `z-genisolist/utils/rsync-stub-generator.py` to generate stub files for testing. Example:

```shell
z-genisolist/utils/rsync-stub-generator.py rsync://rsync.mirrors.ustc.edu.cn/archlinux --dist /srv/repo/archlinux
```

Also `DEBUG_WITH_REPOLIST=1 python3 genindex.py` can help create folders within `HTTPDIR`/`OUTDIR` without the necessity to create stub files one by one.

## Copyright

    Copyright © 2013-2024 USTC Linux User Group <lug@ustc.edu.cn>
    All rights reserved.

    This file is part of Mirrors-index.

    Mirrors-index is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 2 as
    published by the Free Software Foundation.

    Mirrors-index is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Mirrors-index.  If not, see <http://www.gnu.org/licenses/>.

* * *
LUG@USTC
