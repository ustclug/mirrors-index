"""Shared site configuration for source and container deployments."""

import json
from urllib.parse import urlsplit

from utils import CONFIG_FOLDER


def load_site():
    path = CONFIG_FOLDER / "site.json"
    if not path.exists():
        return None
    site = json.loads(path.read_text())
    for key in ("name", "url", "abbr"):
        if not isinstance(site.get(key), str) or not site[key]:
            raise ValueError(f"site.{key} must be a nonempty string")

    def validate_url(value):
        if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
            raise ValueError("Invalid URL")
        if urlsplit(value).scheme not in ("", "http", "https", "mailto"):
            raise ValueError("Unsupported URL scheme")

    for key in ("url", "logo", "statusUrl", "newsFeed"):
        if site.get(key):
            validate_url(site[key])
    for key in ("links", "domains", "monitors"):
        for item in site.get(key, []):
            if not isinstance(item.get("label"), str):
                raise TypeError(f"{key} entries require a label")
            validate_url(item["url"])
    if site.get("announcement"):
        validate_url(site["announcement"]["url"])
    return site


SITE = load_site()


def public_site():
    if SITE is None:
        return None
    public = {
        key: SITE[key]
        for key in (
            "name",
            "url",
            "abbr",
            "description",
            "links",
            "statusUrl",
            "logo",
            "footer",
            "announcement",
            "domains",
            "monitors",
        )
        if key in SITE
    }
    public["schemaVersion"] = 1
    return public


def mirrorz_options():
    path = CONFIG_FOLDER / "genmirrorz.json"
    options = json.loads(path.read_text()) if path.exists() else {}
    if SITE is not None:
        options["base"] = {
            "site": {
                key: SITE[key] for key in ("name", "url", "abbr", "logo") if key in SITE
            }
        }
    return options
