#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import defaultdict
from configparser import ConfigParser
import logging
from argparse import ArgumentParser
from pathlib import Path
import sys
import json
import re
from urllib.parse import urljoin

from utils import CONFIG_FOLDER
from version import LooseVersion

logger = logging.getLogger(__name__)
CONFIG_FILE = Path(CONFIG_FOLDER) / "genisolist.ini"


def get_platform_priority(platform: str) -> int:
    """
    Get the priority of the platform (arch). Higher is more preferred.
    """

    platform = platform.lower()
    if platform in ["amd64", "x86_64", "64bit"]:
        return 100
    elif platform in ["arm64", "aarch64", "arm64v8"]:
        return 95
    elif platform in ["riscv64"]:
        return 95
    elif platform in ["loongson2f", "loongson3"]:
        return 95
    elif platform in ["i386", "i486", "i586", "i686", "x86", "32bit"]:
        return 90
    elif platform in ["arm32", "armhf", "armv7"]:
        return 85
    else:
        return 0


def render(template: str, result: re.Match) -> str:
    """
    Render a template string with matched result.

    A template string contains things like $1, $2, etc. which are replaced with matched groups.

    $0 is also supported, though usually it should not be used.

    BUG: This function does not support $n which n >= 10.
    """

    for i in range(len(result.groups()) + 1):
        grp = result.group(i)
        if f"${i}" in template:
            assert grp is not None, f"Group {i} is not matched with template {template}"
            template = template.replace(f"${i}", grp)
    return template


def render_list(template: str, result: re.Match) -> list:
    """
    Render a template string with matched result, but return a list.

    This function would expect input like "$1 $2 $3" and return ["$1", "$2", "$3"] with replaced values.
    Substrings not starting with "$" would be kept as is in the list
    """

    l = []
    for item in template.split():
        if not item.startswith("$"):
            l.append(item)
        else:
            grp = result.group(int(item[1:]))
            assert (
                grp is not None
            ), f"Group {int(item[1:])} is not matched with template {template}"
            l.append(grp)
    return l


def parse_section(section: dict, root: Path) -> list:
    """
    Parse a distribution section and return a list of sorted file items.

    A section is expected to have following schema:

    {
        "distro": str,
        "listvers": Optional[int] (defaults to 0xff, or 255),
        "location": str,
        "pattern": str,
        "version": str,
        "type": Optional[str] (defaults to ""),
        "platform": str,
        "category": Optional[str] (treats as "os" if not present),
        "key_by": Optional[str] (defaults to "" -- no keying),
        "sort_by": Optional[str] (defaults to sort by version, platform and type),
        "nosort": Optional[bool] (defaults to False),
    }

    Exception could be raised if any of the required fields is missing.

    A "file item" should at least have following schema:

    {
        "path": str (relative path to root),
        "version": str,
        "platform": str,
        "type": str,
    }
    """

    if "location" in section:
        locations = [section["location"]]
    else:
        locations = []
        i = 0
        while True:
            location = section.get(f"location_{i}", None)
            if location is None:
                break
            locations.append(location)
            i += 1
    assert locations, "No location found in section"

    pattern = section.get("pattern", "")
    assert pattern, "No pattern found in section"
    pattern = re.compile(pattern)

    listvers = int(section.get("listvers", 0xFF))
    nosort = bool(section.get("nosort", False))

    files = defaultdict(list)
    for location in locations:
        logger.debug("Location: %s", location)
        file_list = root.glob(location)
        for file_path in file_list:
            relative_path = file_path.relative_to(root)
            logger.debug("File: %s", relative_path)
            result = pattern.search(file_path.name)

            if not result:
                logger.debug("Not matched: %s", file_path)
                continue
            logger.debug("Matched: %r", result.groups())

            file_item = {
                "path": str(relative_path),
                "distro": section["distro"],
                "version": render(section["version"], result),
                "type": render(section.get("type", ""), result),
                "platform": render(section["platform"], result),
            }

            custom_sort_by = section.get("sort_by", "")
            if not custom_sort_by:
                file_item["sort_weight"] = (
                    LooseVersion(file_item["version"]),
                    get_platform_priority(file_item["platform"]),
                    file_item["type"],
                )
            else:
                file_item["sort_weight"] = render_list(custom_sort_by, result)
            logger.debug("File item: %r", file_item)
            # To support key_by, we have to put file_item into a dict first
            key = render(section.get("key_by", ""), result)
            files[key].append(file_item)

    results = []
    for file_list in files.values():
        if not nosort:
            file_list.sort(key=lambda x: x["sort_weight"], reverse=True)

        versions = set()
        for file_item in file_list:
            versions.add(file_item["version"])
            if len(versions) > listvers:
                break
            results.append(file_item)

    return results


def parse_file(file_item: dict, urlbase: str) -> dict:
    """
    Parse a file item (see parse_section() description)
    and return a dictionary with following schema:

    {
        "name": str,
        "url": str,
    }
    """

    url = urljoin(urlbase, file_item["path"])
    if file_item["platform"]:
        desc = "%s (%s%s)" % (
            file_item["version"],
            file_item["platform"],
            ", %s" % file_item["type"] if file_item["type"] else "",
        )
    else:
        desc = file_item["version"]

    return {"name": desc, "url": url}


def gen_from_ini(category: str) -> list:
    """
    Read ini file, parse and return a list. Each item of the list is a dictionary with following schema:

    {
        "distro": str,
        "category": str,
        "urls": [{"name": str, "url": url}]
    }
    """
    ini = ConfigParser()
    if not ini.read(CONFIG_FILE):
        raise FileNotFoundError(f"Cannot find or parse {CONFIG_FILE}")

    # %main% contains root path, url base and distribution sorting
    main = dict(ini.items("%main%"))
    root = Path(main["root"])
    urlbase = main["urlbase"]
    dN = {}
    for key, value in main.items():
        if key.startswith("d"):
            dN[value] = int(key[1:])

    # Following sections represent different distributions each
    # Section name would be ignored. Note that it's possible that a distribution has multiple sections.
    results = defaultdict(list)
    for section in ini.sections():
        if section == "%main%":
            continue
        section = dict(ini.items(section))
        if section.get("category", "os") != category:
            continue
        section_name = section["distro"]
        for file_item in parse_section(section, root):
            results[section_name].append(parse_file(file_item, urlbase))
    
    # Convert results to output
    results = [{"distro": k, "category": category, "urls": v} for k, v in results.items()]
    results.sort(key=lambda x: dN.get(x["distro"], 0xFFFF))

    return results


def get_os_list() -> str:
    return json.dumps(gen_from_ini(category="os"))


def get_app_list() -> str:
    return json.dumps(gen_from_ini(category="app"))


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    parser = ArgumentParser("genisolist")
    parser.add_argument("--os", action="store_true")
    parser.add_argument("--apps", action="store_true")
    args = parser.parse_args()
    if args.os:
        print(get_os_list())
    if args.apps:
        print(get_app_list())
    if not (args.os or args.apps):
        parser.print_help()
