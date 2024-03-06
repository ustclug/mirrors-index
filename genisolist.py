#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import glob
import json
import logging
from urllib.parse import urljoin
from version import LooseVersion
from configparser import ConfigParser
from argparse import ArgumentParser

from utils import CONFIG_FOLDER

logger = logging.getLogger(__name__)
ISOCONFIG_FILE = os.path.join(CONFIG_FOLDER, "genisolist.ini")


def getPlatformPriority(platform):
    platform = platform.lower()
    if platform in ["amd64", "x86_64", "64bit"]:
        return 100
    elif platform in ["i386", "i486", "i586", "i686", "x86", "32bit"]:
        return 90
    else:
        return 0


def parseSection(items, category="os"):
    items = dict(items)
    items_category = items.get("category", "os")
    if items_category != category:
        return

    if "location" in items:
        locations = [items["location"]]
    else:
        locations = []
        i = 0
        while ("location_%d" % i) in items:
            locations.append(items["location_%d" % i])
            i += 1

    pattern = items.get("pattern", "")
    prog = re.compile(pattern)

    images = []
    for location in locations:
        logger.debug("[GLOB] %s", location)

        for imagepath in glob.glob(location):
            logger.debug("[FILE] %s", imagepath)

            result = prog.search(imagepath)

            if not (result):
                logger.debug("[MATCH] None")
                continue
            else:
                logger.debug("[MATCH] %r", result.groups())

            group_count = len(result.groups()) + 1
            imageinfo = {
                "filepath": imagepath,
                "distro": items["distro"],
                "category": items_category,
            }

            for prop in ("version", "type", "platform"):
                s = items.get(prop, "")
                for i in range(0, group_count):
                    if result.group(i):
                        s = s.replace("$%d" % i, result.group(i))
                    else:
                        assert s.find("$%d" % i) == -1
                imageinfo[prop] = s

            logger.debug("[JSON] %r", imageinfo)
            images.append(imageinfo)

    # images.sort(key=lambda k: ( LooseVersion(k['version']),
    images.sort(
        key=lambda k: (
            LooseVersion(k["version"]),
            getPlatformPriority(k["platform"]),
            k["type"],
        ),
        reverse=True,
    )

    i = 0
    versions = set()
    listvers = int(items.get("listvers", 0xFF))
    for image in images:
        versions.add(image["version"])
        if len(versions) <= listvers:
            yield image
        else:
            break


def getDescriptionAndURL(image_info, urlbase):
    url = urljoin(urlbase, image_info["filepath"])
    desc = "%s (%s%s)" % (
        image_info["version"],
        image_info["platform"],
        ", %s" % image_info["type"] if image_info["type"] else "",
    )
    return (desc, url)


def getJsonOutput(url_dict, prio=None):
    if prio is None:
        prio = {}
    raw = []
    for distro in url_dict:
        raw.append(
            {
                "distro": distro,
                "urls": [{"name": l[0], "url": l[1]} for l in url_dict[distro]],
            }
        )

    raw.sort(key=lambda d: prio.get(d["distro"], 0xFFFF))

    return json.dumps(raw)


def getImageList() -> str:
    if os.environ.get("DEBUG_WITH_ISOLIST"):
        with open("examples/isolist.json") as f:
            return f.read()
    return getList("os")


def getAppList() -> str:
    if os.environ.get("DEBUG_WITH_ISOLIST"):
        with open("examples/applist.json") as f:
            return f.read()
    return getList("app")


def getList(category: str = "os") -> str:
    ini = ConfigParser()
    if not (ini.read(ISOCONFIG_FILE)):
        raise Exception("%s not found!" % ISOCONFIG_FILE)
    root = ini.get("%main%", "root")
    urlbase = ini.get("%main%", "urlbase")

    prior = {}
    for name, value in ini.items("%main%"):
        if re.match("d\d+$", name):
            prior[value] = int(name[1:])

    oldcwd = os.getcwd()
    os.chdir(root)

    url_dict = {}
    for section in ini.sections():
        if section == "%main%":
            continue
        for image in parseSection(ini.items(section), category=category):
            if not image["distro"] in url_dict:
                url_dict[image["distro"]] = []

            url_dict[image["distro"]].append(getDescriptionAndURL(image, urlbase))

    os.chdir(oldcwd)

    return getJsonOutput(url_dict, prior)


if __name__ == "__main__":
    import sys

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    parser = ArgumentParser("genisolist")
    parser.add_argument("--images", action="store_true")
    parser.add_argument("--apps", action="store_true")
    args = parser.parse_args()
    if args.images:
        print(getImageList())
    if args.apps:
        print(getAppList())
    if not (args.images or args.apps):
        parser.print_help()
