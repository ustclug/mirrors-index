#!/usr/bin/env python3

import json
import logging
import time
from pathlib import Path
from urllib.parse import urlencode, urljoin

import utils
from utils import CONFIG_FOLDER, get_mirrorz_cname

with open(CONFIG_FOLDER / "gencontent.json") as f:
    USER_CONFIG: dict = json.load(f)

OUTDIR = USER_CONFIG.get("outdir")
"""Default directory for generated output, if configured."""
HTTPDIR = USER_CONFIG.get("httpdir", "/srv/repo")
"""Repository root checked for deployment diagnostics only."""
HELPDIR = USER_CONFIG.get("helpdir")
"""Local help directory override; defaults to the help directory under OUTDIR."""
HELPBASE_MIRRORZ = USER_CONFIG.get(
    "help-mirrorz", "https://help.mirrors.cernet.edu.cn/"
)
MIRROR_NAME = USER_CONFIG.get("mirror-name", "USTC")
MIRRORZ_HELP = USER_CONFIG.get("mirrorz-help", [])
"""Set which repos should use mirrorz-help, if '*' in list then all help links will use mirrorz-help."""
MANUAL_REPOSITORIES = USER_CONFIG.get("manual-repositories", [])

logger = logging.getLogger(__name__)

if MIRRORZ_HELP:
    cname = get_mirrorz_cname()


class YukiMetadataError(RuntimeError):
    pass


def validate_repository_name(name, label="repository name") -> str:
    if not isinstance(name, str) or not name or name in {".", ".."}:
        raise YukiMetadataError(f"{label} must be a non-empty directory name")
    if "/" in name or "\\" in name:
        raise YukiMetadataError(f"{label} must be a single directory name")
    return name


def task_mappings(task: dict) -> list[dict]:
    if not isinstance(task, dict):
        raise YukiMetadataError("Yuki metadata entries must be objects")
    task_name = validate_repository_name(task.get("name"), "task name")
    mappings = task.get("mirrorz")
    if mappings is None:
        return [{"name": task_name}]
    if mappings == {}:
        return []
    if not isinstance(mappings, list):
        raise YukiMetadataError(f"mirrorz for task {task_name!r} must be a list")
    for mapping in mappings:
        if not isinstance(mapping, dict):
            raise YukiMetadataError(
                f"mirrorz entries for task {task_name!r} must be objects"
            )
        validate_repository_name(mapping.get("name"), "mirrorz name")
        if not isinstance(mapping.get("cache", False), bool):
            raise YukiMetadataError(
                f"mirrorz cache for task {task_name!r} must be a boolean"
            )
    return mappings


def fetch_yuki_metadata() -> list[tuple[dict, list[dict]]]:
    snapshots = []
    for endpoint in USER_CONFIG.get("yuki", []):
        if not endpoint.get("homepage") and not endpoint.get("mirrorz"):
            continue
        url = endpoint.get("url")
        if not isinstance(url, str) or not url:
            raise YukiMetadataError("Yuki endpoint URL must be a non-empty string")
        response = utils.get_resp_with_timeout(url, logger=logger)
        if response is None:
            raise YukiMetadataError(f"failed to get Yuki metadata from {url}")
        try:
            metadata = response.json()
        except ValueError as error:
            raise YukiMetadataError(
                f"failed to decode Yuki metadata from {url}"
            ) from error
        if not isinstance(metadata, list) or not metadata:
            raise YukiMetadataError(
                f"Yuki metadata from {url} must be a non-empty list"
            )
        for task in metadata:
            task_mappings(task)
        snapshots.append((endpoint, metadata))
    if not any(endpoint.get("homepage") for endpoint, _metadata in snapshots):
        raise YukiMetadataError("at least one homepage Yuki endpoint is required")
    return snapshots


def metadata_for(snapshots: list[tuple[dict, list[dict]]], purpose: str) -> list[dict]:
    return [
        task
        for endpoint, metadata in snapshots
        if endpoint.get(purpose)
        for task in metadata
    ]


def getMirrorzURL(name):
    params = {"mirror": MIRROR_NAME}
    if cname.get(name):
        name = cname[name]
    return urljoin(HELPBASE_MIRRORZ, name + "?" + urlencode(params))


def testHelpLink(name, outdir=None):
    """Return the configured help URL for a repository, if one is available."""
    if "*" in MIRRORZ_HELP:
        return getMirrorzURL(name)

    helpdir = HELPDIR
    if helpdir is None and (outdir or OUTDIR):
        helpdir = Path(outdir or OUTDIR) / "help"
    if helpdir is not None and (Path(helpdir) / f"{name}.html").is_file():
        return f"/help/{name}.html"

    if name in MIRRORZ_HELP:
        return getMirrorzURL(name)
    return ""


def genRepoList(meta: list[dict] | None = None, outdir=None):
    if meta is None:
        meta = metadata_for(fetch_yuki_metadata(), "homepage")

    homepage_repos: dict[str, int] = {}
    for task in meta:
        mappings = task_mappings(task)
        last_success = task.get("lastSuccess")
        if (
            isinstance(last_success, bool)
            or not isinstance(last_success, int)
            or last_success < 0
        ):
            raise YukiMetadataError(
                f"lastSuccess for task {task['name']!r} must be a non-negative integer"
            )
        for mapping in mappings:
            name = mapping["name"]
            homepage_repos[name] = max(homepage_repos.get(name, 0), last_success)

    if not isinstance(MANUAL_REPOSITORIES, list):
        raise YukiMetadataError("manual-repositories must be a list")
    for name in MANUAL_REPOSITORIES:
        homepage_repos.setdefault(
            validate_repository_name(name, "manual repository name"), 0
        )

    for name in sorted(homepage_repos, key=lambda item: (item.lower(), item)):
        timestamp = homepage_repos[name]
        updated_at = (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
            if timestamp > 0
            else ""
        )
        help_href = testHelpLink(name, outdir=outdir)
        help_text = "Help" if help_href.strip() else ""
        yield (updated_at, help_href, help_text, name)


def getOthers():
    with open(CONFIG_FOLDER / "revproxy.json", "r") as fin:
        info = json.load(fin)
    for repo in info:
        yield (repo["src"], repo["dst"])


if __name__ == "__main__":
    for item in genRepoList():
        print(item)
