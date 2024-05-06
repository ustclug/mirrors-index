#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import sys
import subprocess
import sys
import os
import logging

from utils import CONFIG_FOLDER, get_mirrorz_cname, get_resp_with_timeout
from gencontent import USER_CONFIG as gencontent_config


cname = get_mirrorz_cname()
logger = logging.getLogger(__name__)

with open(os.path.join(CONFIG_FOLDER, "genmirrorz.json")) as f:
    options = json.load(f)
    base = options["base"]
    skiplist = options.get("skip", [])

metas = []
for yuki_endpoint in gencontent_config.get("yuki", []):
    if yuki_endpoint.get("mirrorz"):
        url = yuki_endpoint["url"]
        this_metas = get_resp_with_timeout(url)
        if not this_metas:
            logger.error(f"failed to get {url}")
            continue
        try:
            this_metas = this_metas.json()
        except json.JSONDecodeError:
            logger.error(f"failed to decode json from {url}")
            continue
        if not this_metas:
            logger.error(f"empty json from {url}")
            continue
        metas.extend(this_metas)


def name_func(name: str) -> str:
    if name in cname:
        return cname[name]
    else:
        return name


def iso(iso_orig: list) -> None:
    # modify iso_orig inplace
    for i in iso_orig:
        i["distro"] = name_func(i["distro"])
        if not i.get("category"):
            # fallback to OS (iso) if not exist.
            i["category"] = "os"


def size(bytes: int) -> str:
    mib = bytes / 1024 / 1024
    if mib < 1024:
        return f"{mib:.2f} MiB"
    gib = mib / 1024
    if gib < 1024:
        return f"{gib:.2f} GiB"
    tib = gib / 1024
    return f"{tib:.2f} TiB"


def parse_repo_with_meta(repolist: list, meta: dict) -> dict:
    content_list = []
    content_hash = {}
    for i in repolist:
        _, help_url, _, name = i
        cname = name_func(name)
        content_hash[cname.lower()] = len(content_list)
        content_list.append(
            {
                "cname": cname,
                "desc": "",  # now we don't have desc yet...
                "url": f"/{name}",
                "status": "U",
                "help": help_url,
                "upstream": "",
            }
        )
    # now we add data to content_list with meta!
    for i in meta:
        name = i["name"]
        if name in skiplist:
            continue
        name = name_func(name)
        try:
            try:
                ind = content_hash[name.lower()]
            except KeyError:
                ind = content_hash[
                    name.lower().split(".")[0]
                ]  # fix repo name like "kubernetes.apt"
            next_run = i.get("nextRun")
            last_success = i.get("lastSuccess")
            if next_run < 0:
                content_list[ind][
                    "status"
                ] = "P"  # negative next_run means cron date set to 2/30 or 2/31 (unreachable)
            elif i["syncing"]:
                content_list[ind]["status"] = "Y" + str(i.get("prevRun"))
                if last_success:
                    content_list[ind]["status"] += "O" + str(last_success)
            elif i["exitCode"] == 0:
                content_list[ind]["status"] = "S" + str(last_success)
            else:
                content_list[ind]["status"] = "F" + str(i.get("prevRun"))
                if last_success:
                    content_list[ind]["status"] += "O" + str(last_success)
            if next_run > 0:
                content_list[ind]["status"] += "X" + str(next_run)
            content_list[ind]["size"] = size(i["size"])
            content_list[ind]["upstream"] = i["upstream"]
        except KeyError:
            print(f"failed to parse {i['name']}", file=sys.stderr)
    return content_list


def disk_info(site: dict) -> None:
    # TODO(portability): This now only works on mirrors4
    lug_repo = subprocess.check_output(
        "df -h | grep lug-repo | awk {'print $3, $2'}", shell=True
    ).decode("utf-8")
    site["disk"] = lug_repo.replace(" ", "/")


def getMirrorzJson(repolist, isolist, applist):
    if type(isolist) is str:
        isolist = json.loads(isolist)
    if type(applist) is str:
        applist = json.loads(applist)
    for i in applist:
        i["category"] = "app"

    disk_info(base["site"])
    iso(isolist)
    iso(applist)
    mirrors = parse_repo_with_meta(repolist, metas)

    mirrorz = base
    mirrorz["info"] = isolist + applist
    mirrorz["mirrors"] = mirrors

    return json.dumps(mirrorz)


if __name__ == "__main__":
    import genisolist
    import gencontent

    isolist = genisolist.get_os_list()
    applist = genisolist.get_app_list()
    repolist = gencontent.genRepoList()

    print(getMirrorzJson(repolist, isolist, applist))
