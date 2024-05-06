# mirrors-index

Help documentation source code: https://github.com/ustclug/mirrorhelp/

## Dependencies

* python3
* python3-requests
* python3-jinja2
* systemd (optional)

## Install

Assuming that your metadata is stored in `/srv/rsync-attrs`. Otherwise, you should modify the `HTTPDIR` variable in gencontent.py (by gencontent.json), and root attribute in genisolist.ini.

Metadata now is generated from rsync-huai hook after every sync by yuki.

### Current Method

Add the following line to your crontab (`crontab -e`)

```
10  *   * * *   /usr/bin/python3 /home/mirror/scripts/mirrors-index/genindex.py -o /srv/www-misc/index.html 2> /dev/null
```

It will update every hour at minute 10.

### Alternative Method

Copy all the systemd service files (`mirrors-index.service`, `mirrors-index.timer`,
`mirrors-index.path`) from `services/` dir into `/etc/systemd/system/`.
Then enable them and start the timer and the path file.

### Previous Method

The following method is obsolete, because /srv/www only contains symlinks.

Add a following line to incrontab:

```/srv/www IN_CREATE,IN_DELETE,IN_MOVE /home/mirror/newindex/genindex.py```

The crontab file was also used to trigger the update based on time before.
Use `crontab -l -u mirror` to check the line that has been commented out for now.

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

Then `apt update && apt install -y python3 python3-requests python3-jinja2` to install dependencies.

`mkdir /srv/rsync-attrs` to create a fake directory for metadata, and `python3 -m http.server --directory /srv/rsync-attrs &` at `/workspace` to start a HTTP server at port 8000 for host browser access.

`python3 genindex.py` to generate the index page. Note that this repo currently does not contain webfont-related files yet.

If you need to debug genisolist, `DEBUG_WITH_ISOLIST=1 python3 genindex.py` can generate a full list without the necessity to create stub files one by one.

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
