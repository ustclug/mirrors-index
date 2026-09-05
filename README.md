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
make install WEBROOT=/srv/www-misc
python3 genindex.py -o /srv/www-misc/index.html
```

`make install` installs the hashed JavaScript bundles, fonts, and `/status/`
page. It does not generate the homepage. The periodic job only needs Python and
uses the build manifest left by `make build`; Node and package managers are not
involved in hourly updates. See `vendor/preact/VENDORING.md` for the vendored
source and update procedure.

The generated homepage contains a minimal repository list for browsers where
JavaScript is unavailable. The full interface is rendered from versioned JSON
embedded in that same file, so no additional homepage data request is needed.

### Periodic updates

Install the service and timer, then enable the timer:

```shell
install -m 0644 services/mirrors-index.service services/mirrors-index.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now mirrors-index.timer
```

The timer regenerates the homepage every hour at minute 10. Run an initial
generation immediately after deployment with:

```shell
systemctl start mirrors-index.service
```

### Locales

Install zh_CN locales since the `genisolist.ini` file contains Chinese characters.

## Development

Here we introduce how to develop this project on your personal computer (without polluting host's filesystem environment).

Create a Debian container:

```shell
# fish shell
docker run --rm -it -p 8000:8000 -e TZ=Asia/Shanghai -v $(pwd):/workspace ustclug/debian:12
# bash shell
docker run --rm -it -p 8000:8000 -e TZ=Asia/Shanghai -v $PWD:/workspace ustclug/debian:12
```

Then install the Python dependencies above, Node.js, esbuild, TypeScript, pnpm,
and Chromium. pnpm is only needed to install the Playwright development
dependency: run `pnpm install --frozen-lockfile --ignore-scripts` once.

`mkdir /srv/repo` to create a fake directory for metadata, and `python3 -m http.server --directory /srv/repo &` at `/workspace` to start a HTTP server at port 8000 for host browser access.

Use these entry points during development:

```shell
make build       # type-check and create production assets under dist/
make dev         # watch the TypeScript entry points
make format      # format project-owned Python files with Ruff
make lint        # check Ruff formatting and lint rules
make test        # Python unit tests and Playwright browser tests
python3 genindex.py -o dist/index.html
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
