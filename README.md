# mirrors-index

This repo contains frontend source code (`/` and `/status/`) of USTC Mirror, and could be used to build third-party mirror sites. This is intended to be used with [Yuki](https://github.com/ustclug/Yuki) mirror management tool.

For *Help documentation*, see: https://github.com/ustclug/mirrorhelp/

## Dependencies

All of these can be fetched from Debian 13 official repo:

* python3
* python3-requests
* python3-jinja2
* nodejs
* esbuild
* typescript
* systemd (optional: the timer to run generation)

pnpm and Playwright are only needed for e2e tests (Debian bug [#1153120](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1153120) makes it necessary to be installed from npmjs); ruff and ty are only needed for Python linting and type checking. None of them are required for deployment.

## Preparation

genisolist is a submodule of [mirrorz-org/genisolist](https://github.com/mirrorz-org/genisolist/), so please checkout the submodule first:

```shell
git submodule update --init --recursive
```

## Configuration

Site configuration files live in `config/`.

### `gencontent.json`

`baseURL` is required and must be the HTTP(S) origin that serves `/status/json`, for example `https://example.com`; the generator and the browser both request that endpoint. For multiple Yuki instances, aggregate their task arrays in the web server (with lua or njs in Nginx, for example) and serve the result at `/status/json`.

A repo could have multiple Yuki tasks. Yuki tasks are mapped to repositories as follows: `mirrorz.name` must exactly match the published top-level directory, including case; a task without a `mirrorz` field uses its task name, while `mirrorz: []` excludes it.

Optional keys:

* `cname-upstream`: optional URL for the MirrorZ canonical-name mapping. Each generation first fetches this URL (default `https://mirrors.cernet.edu.cn/static/json/cname.json`), even when a local `cname.json` exists.
* `manual-repositories`: repository names to include without Yuki metadata; their Last Update column is left blank.
* `outdir`: default output directory, overridden by `--outdir` or the `OUTDIR` environment variable.
* `httpdir`: repository root checked as a deployment diagnostic; defaults to `/srv/repo`.
* `helpdir`: local directory containing `help/<repository>.html`; links are emitted only when the file exists, and the default is `<outdir>/help`.
* `mirror-name`: name used in MirrorZ help links; defaults to `USTC`.
* `mirrorz-help` and `help-mirrorz`: list of repositories whose help links use MirrorZ (`"*"` for all) and the MirrorZ help base URL, which defaults to `https://help.mirrors.cernet.edu.cn/`.

### `descriptions.json`

Object mapping repository names to description text, matched case-insensitively and used by both the homepage and MirrorZ output.

### `genmirrorz.json`

`skip` lists repository names excluded from generated output (case-insensitive). `base` is copied into `mirrorz.json`; its `site` object typically sets `url`, `abbr`, `name`, `logo`, `logo_darkmode`, `homepage`, `issue`, `request`, `email`, `group`, and `big`.

### `cname.json`

Canonical-name mapping used in MirrorZ output. The generator reads this local file if the upstream fetch fails.

### `genisolist.ini`

ISO discovery configuration passed to genisolist, including the files under `z-genisolist/includes/`. Install zh_CN locales because the file contains Chinese characters.

## Build and deploy

The browser application uses the Preact copy under `vendor/`, while repository discovery and page data generation remain in Python. Production does not need npm or pnpm. Build on the production machine and install the static application into the web root:

```shell
make build  # only run this when the frontend source code is updated
python3 genindex.py --outdir /srv/www/
make install WEBROOT=/srv/www
```

`make install` installs the already-built static homepage, hashed JavaScript and CSS bundles, fonts, and `/status/` page. It does not rebuild them. The periodic job only needs Python.

The `mirror` user running the periodic job must be able to create and replace files in `/srv/www/` and `/srv/www/static/`.

Generation atomically updates `/static/json/index.json`, `index-nojs.html`, and `/static/json/mirrorz.json`.

## Periodic updates

Install the service and timer, then enable the timer:

```shell
install -m 0644 services/mirrors-index.service services/mirrors-index.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now mirrors-index.timer
```

The timer regenerates the homepage data files every hour. Run an initial generation immediately after deployment with:

```shell
systemctl start mirrors-index.service
```

## Development

This project supports devcontainer (or you can start a container yourself). It's recommended to do development inside the (Debian 13) container, as things might be different with newer or older versions of esbuild or TypeScript.

If you prefer to run container yourself, build the development image manually:

```shell
docker build -f Dockerfile.dev -t mirrors-index-dev .
```

Start a shell using the source tree included in the image:

```shell
docker run --rm -it -v "$(pwd):/workspace" -p 8000:8000 mirrors-index-dev
```

Use these entry points during development:

```shell
make build       # type-check and create production assets under dist/
make dev         # build and watch file changes
make format      # format project-owned Python files with Ruff
make lint        # check Ruff formatting and lint rules
make test        # Python unit tests and Playwright browser tests
make example     # populate /srv/repo with a small representative repository tree and example sync data under dist/status/json
python3 genindex.py --outdir dist/
python3 -m http.server --directory dist
```

## MirrorZ JSON generator container

If you only need to generate mirrorz.json info from Yuki and local disk state, you can use our container image (`ghcr.io/ustclug/mirrors-index-mirrorz`) for this.

Mount a read-only directory at `/config` containing these two files.
For example, `gencontent.json` can contain:

```json
{"baseURL":"https://mirror.example.org"}
```

In `genmirrorz.json`, supply your site's own details:

```json
{"base":{"site":{"url":"https://mirror.example.org","abbr":"EX","name":"Example Mirror"}}}
```

Mount a writable directory at `/output` and serve its `mirrorz.json`.
The image runs once, replacing the file after successful generation.

ISO discovery is optional. To enable it, mount the repository tree read-only
at `/srv/repo` and add `genisolist.ini` to the config directory. An example:

```ini
[%main%]
root = /srv/repo/
urlbase = /

!include /app/includes/distro.ini
!include /app/includes/os/**/*.ini
!include /app/includes/app/**/*.ini
```

For local help links, mount your help directory read-only and set `helpdir`
to its container path. Optional `descriptions.json` overrides the bundled
descriptions.

## Copyright

### License

    Copyright © 2013-2026 USTC Linux User Group <lug@ustc.edu.cn>
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

### Extra notice for third-party deployments

You **MUST** clearly indicate that your site is **NOT affiliated** with USTC Linux User Group, and provide a link to the original project. You **MUST** also publicize your source code with GPLv2.

* * *

LUG@USTC
