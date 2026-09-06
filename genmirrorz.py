#!/usr/bin/env python3


import copy
import json
import logging
import shutil
import subprocess
from dataclasses import dataclass

import gencontent
from utils import CONFIG_FOLDER, get_mirrorz_cname

cname = get_mirrorz_cname()
logger = logging.getLogger(__name__)

with open(CONFIG_FOLDER / "genmirrorz.json") as f:
    options = json.load(f)
    base = options["base"]
    skiplist = options.get("skip", [])
    descriptions = options.get("descriptions", {})
    descriptions_by_name = {
        name.lower(): description for name, description in descriptions.items()
    }


@dataclass(frozen=True)
class RepoContribution:
    task_name: str
    cache: bool
    disable: bool
    syncing: bool
    exit_code: int
    last_success: int
    prev_run: int
    next_run: int
    size_bytes: int
    upstream: str

    @property
    def paused(self) -> bool:
        return self.disable or self.next_run < 0


def name_func(name: str) -> str:
    return cname.get(name, name)


def skipped_repo(name: str) -> bool:
    return name.lower() in {item.lower() for item in skiplist}


def repo_description(name: str) -> str:
    description = descriptions_by_name.get(name.lower())
    if not description:
        logger.warning("missing MirrorZ description for %s", name)
        return ""
    return description


def collect_repo_contributions(meta: list[dict]) -> dict[str, list[RepoContribution]]:
    grouped = {}
    for task in meta:
        mappings = gencontent.task_mappings(task)
        task_name = task["name"]
        if skipped_repo(task_name):
            continue
        numeric_fields = ["exitCode", "lastSuccess", "prevRun", "nextRun", "size"]
        if any(
            isinstance(task.get(field), bool) or not isinstance(task.get(field), int)
            for field in numeric_fields
        ):
            raise gencontent.YukiMetadataError(
                "runtime and size fields must be integers"
            )
        if task["size"] < 0:
            raise gencontent.YukiMetadataError("size must not be negative")
        if not isinstance(task.get("syncing"), bool):
            raise gencontent.YukiMetadataError("syncing must be a boolean")
        if not isinstance(task.get("disable", False), bool):
            raise gencontent.YukiMetadataError("disable must be a boolean")
        if not isinstance(task.get("upstream", ""), str):
            raise gencontent.YukiMetadataError("upstream must be a string")
        contribution_fields = {
            "task_name": task_name,
            "disable": bool(task.get("disable", False)),
            "syncing": task["syncing"],
            "exit_code": task["exitCode"],
            "last_success": task["lastSuccess"],
            "prev_run": task["prevRun"],
            "next_run": task["nextRun"],
            "size_bytes": task["size"],
            "upstream": task.get("upstream", ""),
        }
        for mapping in mappings:
            logical_name = mapping["name"]
            if skipped_repo(logical_name):
                continue
            grouped.setdefault(logical_name, []).append(
                RepoContribution(
                    cache=bool(mapping.get("cache", False)),
                    **contribution_fields,
                )
            )
    return grouped


def earliest_positive(values) -> int | None:
    positive = [value for value in values if value > 0]
    return min(positive) if positive else None


def latest_positive(values) -> int | None:
    positive = [value for value in values if value > 0]
    return max(positive) if positive else None


def status_with_timestamp(status: str, timestamp: int | None) -> str:
    return status + (str(timestamp) if timestamp is not None else "")


def aggregate_status(contributions: list[RepoContribution]) -> str:
    if any(item.cache for item in contributions):
        return "C"

    active = [item for item in contributions if not item.paused]
    if not active:
        return "P"

    failed = [item for item in active if not item.syncing and item.exit_code != 0]
    syncing = [item for item in active if item.syncing]
    last_success = earliest_positive(item.last_success for item in active)
    next_run = earliest_positive(item.next_run for item in active)

    if failed:
        status = status_with_timestamp(
            "F", latest_positive(item.prev_run for item in failed)
        )
        if last_success is not None:
            status += f"O{last_success}"
    elif syncing:
        status = status_with_timestamp(
            "Y", earliest_positive(item.prev_run for item in syncing)
        )
        if last_success is not None:
            status += f"O{last_success}"
    else:
        status = status_with_timestamp("S", last_success)

    if next_run is not None:
        status += f"X{next_run}"
    return status


def aggregate_contributions(contributions: list[RepoContribution]) -> dict:
    upstreams = {item.upstream for item in contributions if item.upstream}
    return {
        "status": aggregate_status(contributions),
        "size": size(max(item.size_bytes for item in contributions)),
        "upstream": upstreams.pop() if len(upstreams) == 1 else "",
    }


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


def parse_repo_with_meta(repolist: list, meta: list[dict]) -> list[dict]:
    content_list = []
    content_hash = {}
    for i in repolist:
        _, help_url, _, name = i
        if skipped_repo(name):
            continue
        content = {
            "cname": name_func(name),
            "desc": repo_description(name),
            "url": f"/{name}",
            "status": "U",
            "help": help_url,
            "upstream": "",
        }
        content_hash[name] = len(content_list)
        content_list.append(content)
    for name, contributions in collect_repo_contributions(meta).items():
        ind = content_hash.get(name)
        if ind is None:
            tasks = ", ".join(sorted({item.task_name for item in contributions}))
            logger.warning(
                "Yuki task(s) %s map to unpublished MirrorZ repository %s",
                tasks,
                name,
            )
            continue
        content_list[ind].update(aggregate_contributions(contributions))
    deduplicated = []
    canonical_names = {}
    for content in content_list:
        key = content["cname"].lower()
        if key in canonical_names:
            deduplicated[canonical_names[key]] = content
        else:
            canonical_names[key] = len(deduplicated)
            deduplicated.append(content)
    return deduplicated


def disk_info(site: dict) -> None:
    # TODO(portability): This now only works on mirrors4
    repo_zfs = subprocess.check_output(
        "zfs get -Hp -o value used,available pool0/repo", shell=True
    ).decode("utf-8")
    used, available = repo_zfs.split()
    used = int(used)
    available = int(available)
    site["disk"] = f"{size(used)} / {size(used + available)}"


def add_disk_info_if_available(site: dict) -> None:
    if shutil.which("zfs") is None:
        logger.warning("zfs is not available; skipping repository size")
        return
    disk_info(site)


def getMirrorzJson(repolist, isolist, meta=None):
    mirrorz = copy.deepcopy(base)
    add_disk_info_if_available(mirrorz["site"])
    iso(isolist)
    if meta is None:
        meta = gencontent.metadata_for(gencontent.fetch_yuki_metadata(), "mirrorz")
    mirrors = parse_repo_with_meta(repolist, meta)

    mirrorz["info"] = isolist
    mirrorz["mirrors"] = mirrors

    return json.dumps(mirrorz, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    from utils import get_isolist

    snapshots = gencontent.fetch_yuki_metadata()
    isolist = get_isolist()
    repolist = gencontent.genRepoList(gencontent.metadata_for(snapshots, "homepage"))

    print(
        getMirrorzJson(repolist, isolist, gencontent.metadata_for(snapshots, "mirrorz"))
    )
