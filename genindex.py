#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
#import urlparse
from urllib import parse as urlparse
import urllib
import fnmatch
#from cStringIO import StringIO as StrIO
from io import StringIO as StrIO
from genisolist import getImageList

BASEDIR = os.path.dirname(__file__)
HTTPDIR = '/srv/www'

# When debugging, pass an argument to the script to override output file path.
OUTFILE = os.path.join(HTTPDIR, 'index.html')
# Directories match these glob will be ignored.
EXCLUDE = ("tmpfs", ".*")


def addStatic (filepath, str_out):
    fin = open(filepath)
    str_out.write(fin.read())
    fin.close()


# A unreliable workaround for nested repos. See comments in main program.
def CTimeWA (dirpath):
    ctime = 0
    for subd in os.listdir(dirpath):
        subdirpath = os.path.join(dirpath, subd)
        if not os.path.isdir(subdirpath):
            continue

        _ctime = os.stat(subdirpath).st_ctime
        if _ctime > ctime:
            ctime = _ctime

    return ctime


def testHelpLink (name):
    URLBASE = "https://lug.ustc.edu.cn/wiki/mirrors/help/"
    url = urlparse.urljoin(URLBASE, name)

    try:
        #html = urllib2.urlopen(url, timeout = 4)
        html = urllib.request.urlopen(url, timeout = 4)
    except (urllib.error.URLError, urllib.error.HTTPError):
        return False

    for line in html:
        if '<h1 class="sectionedit1"' in line:
            html.close()
            return False if "该主题尚不存在" in line else True

    return True


if __name__ == '__main__':
    if len(sys.argv) > 1:
        OUTFILE = sys.argv[1]
        print "Output HTML to '%s'" % OUTFILE

    output = StrIO()

    addStatic(os.path.join(BASEDIR, 'header.html'), output)

    output.write('<table cellpadding="0" cellspacing="0" class="filelist">')
    output.write("""
        <thead>
          <tr id="firstline">
            <th id="name">Folder</th>
            <th class="update">Last Update</th>
            <th id="help">Help</th>
          </tr>
        </thead>"""
    )

    now = time.time()
    for d in sorted(os.listdir(HTTPDIR), key = lambda s: s.lower()):
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
        if time.time() - ctime > 3600*24*2:
            _ctime = CTimeWA(fpath)
            if _ctime > ctime:
                ctime = _ctime

        output.write("""
            <tr>
              <td class="filename"><a href="/{DIR}">{DIR}</a></td>
              <td class="filetime">{MODTIME}</td>
              <td class="help" >
                <a href="https://lug.ustc.edu.cn/wiki/mirrors/help/{DIR}">
                  {HELP}
                </a>
              </td>
            </tr>
        """.format(
            DIR = d,
            MODTIME = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ctime)),
            HELP = "Help" if testHelpLink(d) else ""
        ))

    output.write("</table>")

    addStatic(os.path.join(BASEDIR, 'middle.html'), output)
    output.write(getImageList())
    addStatic(os.path.join(BASEDIR, 'footer.html'), output)

    # Actually write file at last, so runtime errors won't cause broken page.
    fout = open(OUTFILE, 'w')
    fout.write(output.getvalue())
    fout.close()

    output.close()

