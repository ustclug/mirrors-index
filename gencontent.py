#!/usr/bin/env python3

import json
import logging
import time
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit

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


def fetch_yuki_metadata() -> list[dict]:
    base_url = USER_CONFIG.get("baseURL")
    error_message = "baseURL must be an HTTP(S) origin without a path, credentials, query, or fragment"
    if not isinstance(base_url, str) or not base_url:
        raise YukiMetadataError(error_message)
    try:
        parsed = urlsplit(base_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise YukiMetadataError(error_message)
    except ValueError as error:
        raise YukiMetadataError(error_message) from error
    url = urljoin(base_url, "/status/json")
    response = utils.get_resp_with_timeout(url, logger=logger)
    if response is None:
        raise YukiMetadataError(f"failed to get Yuki metadata from {url}")
    try:
        metadata = response.json()
    except ValueError as error:
        raise YukiMetadataError(f"failed to decode Yuki metadata from {url}") from error
    if not isinstance(metadata, list) or not metadata:
        raise YukiMetadataError(f"Yuki metadata from {url} must be a non-empty list")
    for task in metadata:
        task_mappings(task)
    return metadata


def get_mirrorz_url(name):
    params = {"mirror": MIRROR_NAME}
    if cname.get(name):
        name = cname[name]
    return urljoin(HELPBASE_MIRRORZ, name + "?" + urlencode(params))


def get_help_link(name, outdir=None):
    """Return the configured help URL for a repository, if one is available."""
    if "*" in MIRRORZ_HELP:
        return get_mirrorz_url(name)

    helpdir = HELPDIR
    output_directory = outdir or OUTDIR
    if helpdir is None and output_directory:
        helpdir = Path(output_directory) / "help"
    if helpdir is not None and (Path(helpdir) / f"{name}.html").is_file():
        return f"/help/{name}.html"

    if name in MIRRORZ_HELP:
        return get_mirrorz_url(name)
    return ""


def generate_repo_list(meta: list[dict] | None = None, outdir=None):
    if meta is None:
        meta = fetch_yuki_metadata()

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
        help_href = get_help_link(name, outdir=outdir)
        help_text = "Help" if help_href.strip() else ""
        yield (updated_at, help_href, help_text, name)


if __name__ == "__main__":
    for item in generate_repo_list():
        print(item)
