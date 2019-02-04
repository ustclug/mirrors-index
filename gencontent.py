#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
from urllib.parse import urljoin
import requests
import fnmatch

HTTPDIR = '/srv/rsync-attrs'

EXCLUDE = ("tmpfs", ".*")
"""Directories match these glob will be ignored."""


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


def testHelpLink(name):
    URLBASE_SPHI = "http://mirrors.ustc.edu.cn/help/"
    sphinx_exist = True
    url = urljoin(URLBASE_SPHI, name + ".html")
    try:
        html = requests.get(url, timeout=1)
    except:
        sphinx_exist = False
    if sphinx_exist == True and "404 Not Found" not in html.text:
        return url

    URLBASE_DOKU = "https://lug.ustc.edu.cn/wiki/mirrors/help/"
    url = urljoin(URLBASE_DOKU, name)

    try:
        html = requests.get(url, timeout=4)
    except:
        return ''

    return "" if "该主题尚不存在" in html.text else url



def genRepoList():
    for d in sorted(os.listdir(HTTPDIR), key=str.lower):
        fpath = os.path.join(HTTPDIR, d)

        if not os.path.isdir(fpath) or \
                any(fnmatch.fnmatch(d, p) for p in EXCLUDE):
            continue

        # Change time is lastsync time if sync destination is exactly the same
        # top-level dir of http. However, some repos are divided to several
        # sub-dirs which are actually sync-ed instead of top-level directory.
        # We need to check these sub-dirs to find correct lastsync time.
        ctime = os.stat(fpath).st_ctime

        # Since checking all sub-dirs wastes much time, the script just check
        # repos whose top-level dirs have a old change time.
        if time.time() - ctime > 3600 * 24 * 2:
            _ctime = CTimeWA(fpath)
            if _ctime > ctime:
                ctime = _ctime

        help_href = testHelpLink(d)
        help_text = 'Help' if help_href.strip() else ""
        
        yield (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ctime)),
               help_href,
               help_text,
               d)

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
