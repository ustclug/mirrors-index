#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
from urllib.parse import urlencode, urljoin
from urllib.parse import urlparse
import requests
import fnmatch
import json
import utils
import logging

with open(os.path.join(os.path.dirname(__file__), 'gencontent.json')) as f:
    USER_CONFIG: dict = json.load(f)

HTTPDIR = USER_CONFIG.get("httpdir", '/srv/rsync-attrs')
HELPBASE_SPHI = USER_CONFIG.get("help-sphinx", "http://mirrors.ustc.edu.cn/help/")
HELPBASE_MIRRORZ = USER_CONFIG.get("help-mirrorz", "https://help.mirrors.cernet.edu.cn/")
MIRROR_NAME = USER_CONFIG.get("mirror-name", "USTC")

EXCLUDE = ("tmpfs", ".*")
"""Directories match these glob will be ignored."""
UPDATE_DATE_EXCLUDE = USER_CONFIG["extra-exclude"]
"""Directories match these names will not have update date calculated."""
MIRRORZ_HELP = USER_CONFIG.get("mirrorz-help", [])
"""Set which repos should use mirrorz-help, if '*' in list then all help links will use mirrorz-help."""

logger = logging.getLogger(__name__)


def CTimeWA(dirpath):
    """A unreliable workaround for nested repos.
    See comments in main program.
    """
    ctime = 0
    for subd in os.listdir(dirpath):
        subdirpath = os.path.join(dirpath, subd)
        if not os.path.isdir(subdirpath):
            continue

        _ctime = os.stat(subdirpath).st_ctime
        if _ctime > ctime:
            ctime = _ctime

    return ctime


def getMirrorzURL(name):
    params = {"mirror": MIRROR_NAME}
    return urljoin(HELPBASE_MIRRORZ, name + "?" + urlencode(params))


def testHelpLink(name):
    """
    For non-ustc mirrors, we can use mirrorz-help to generate help links.
    Currently we don't check the existence of help pages.
    """
    if "*" in MIRRORZ_HELP:
        return getMirrorzURL(name)

    """
    Check if the help page exists on sphinx.
    """
    sphinx_exist = True
    url = urljoin(HELPBASE_SPHI, name + ".html")
    try:
        html = requests.get(url, timeout=1)
    except:
        sphinx_exist = False
    if sphinx_exist == True and "404 Not Found" not in html.text:
        return urlparse(url).path

    """
    If user specified the help page exists on mirrorz-help, we use it.
    """
    if name in MIRRORZ_HELP:
        return getMirrorzURL(name)

    return ""



def genRepoList():
    # get remote-yuki repo list from gencontent.json
    remote_repos = {}
    for yuki_endpoint in USER_CONFIG.get("remote-yuki", []):
        resp = utils.get_resp_with_timeout(yuki_endpoint)
        if resp is None:
            continue
        try:
            resp = resp.json()
            for repo in resp:
                remote_repos[repo["name"]] = repo["lastSuccess"]
        except Exception as e:
            logger.warning("Failed to parse remote-yuki response: {}".format(e))
    for d in sorted(os.listdir(HTTPDIR), key=str.lower):
        fpath = os.path.join(HTTPDIR, d)

        if not os.path.isdir(fpath) or \
                any(fnmatch.fnmatch(d, p) for p in EXCLUDE):
            continue

        # Change time is lastsync time if sync destination is exactly the same
        # top-level dir of http. However, some repos are divided to several
        # sub-dirs which are actually sync-ed instead of top-level directory.
        # We need to check these sub-dirs to find correct lastsync time.
        if d in remote_repos:
            ctime = remote_repos[d]
        elif d in UPDATE_DATE_EXCLUDE:
            ctime = 0
        else:
            ctime = os.stat(fpath).st_ctime

            # Since checking all sub-dirs wastes much time, the script just check
            # repos whose top-level dirs have a old change time.
            if time.time() - ctime > 3600 * 24 * 2:
                _ctime = CTimeWA(fpath)
                if _ctime > ctime:
                    ctime = _ctime

        ctime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ctime)) if ctime != 0 else ""
        help_href = testHelpLink(d)
        help_text = 'Help' if help_href.strip() else ""

        yield (ctime_str, help_href, help_text, d)

def getOthers():
    _d = os.path.dirname(os.path.realpath(__file__))
    info = None
    with open(os.path.join(_d, 'revproxy.json'), 'r') as fin:
        info = json.load(fin)
    for repo in info:
        yield (repo['src'], repo['dst'])

if __name__ == '__main__':
    for i in genRepoList():
        print(i)
