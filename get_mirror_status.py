#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 USTC LUG
#               2011 Cheng Zhang
#
# Origin Author: Cheng Zhang <StephenPCG@gmail.com>
# Edit by:       Yuanchong Zhu <redsky0802@gmail.com>
# Maintainer:    Yuanchong Zhu <redsky0802@gmail.com>

import os.path, time, datetime
import re
import json

LOG_BASE = os.path.join(os.getenv("HOME"), "log/")
ETC_BASE = os.path.join(os.getenv("HOME"), "etc/")
BIN_BASE = os.path.join(os.getenv("HOME"), "bin/")

SIZE_UNIT = {
        0 : " B",
        1 : "KB",
        2 : "MB",
        3 : "GB",
        4 : "TB"
        }

HTML_TAGS = {
        "begin_td" : "<td>",
        "end_td" : "</td>",
        "begin_tr" : "<tr>",
        "end_tr" : "</tr>\n"
        }


def toHumanReadableSize(size_in_byte):
    ''' convert size in byte to human readable size, B/KB/MB/GB '''
    new_size = size_in_byte
    new_unit = 0
    while new_size >= 1024.0:
        new_size /= 1024.0
        new_unit += 1

    return "%.2f %s" % (new_size, SIZE_UNIT[new_unit])

def getLogFileName(log_path, script_type):
    ''' get log filename for archive, without postfix '.0' '''
    if script_type == "cd-mirror":
        return LOG_BASE + log_path + "/rsync-debian-cd-mirror.log"
    elif script_type == "ftpsync":
        return LOG_BASE + log_path + "/rsync-" + script_type + "-" + log_path + ".log"
    else:
        return LOG_BASE + log_path + "/" + script_type + "-" + log_path + ".log"

def getSyncStatus(log_file_name):
    ''' get archive sync status '''
    if os.path.isfile(log_file_name):
        return "running"
    elif os.path.isfile(log_file_name + ".0"):
        return "finished"
    else:
        return "unknown"

def getSyncErrorAndArchiveSize(log_file_name):
    ''' parse log file, get ERROR status and archive size, returns a tuple (error, size, size_in_byte) '''
    
    if log_file_name == "":
        return False, "", 0

    log_file_name = log_file_name + ".0"
    if not os.path.isfile(log_file_name):
        return False, "", 0
    error = False
    size = ""
    size_in_byte = 0
    for line in open(log_file_name):
        if line.find("ERROR") != -1 or line.find("rsync error") != -1:
            error = True
        if line.find("total size is") != -1:
            size_in_byte = int(re.search('total size is (\d+)', line).group(1))
            size = toHumanReadableSize(size_in_byte)
    return error, size, size_in_byte

def getArchiveUpstream(log_path, sync_script):
    ''' get archive upstream '''
    if sync_script == "cd-mirror":
        etc_file = ETC_BASE + "debian-cd-mirror.conf"
    else:
        etc_file = ETC_BASE + sync_script + "-" + log_path + ".conf"
    upstream = ""
    path = ""
    for line in open(etc_file):
        if re.search("^RSYNC_HOST", line):
            upstream = re.search('^RSYNC_HOST.+"(.+)"', line).group(1)
        if re.search("^RSYNC_PATH", line):
            path = re.search('^RSYNC_PATH.+"(.+)"', line).group(1)
    return "rsync://" + upstream + "/" + path

def getArchiveSyncTime(log_file_name, sync_status):
    ''' get archive sync time '''
    if sync_status == "running":
        if os.path.isfile(log_file_name):
            return datetime.datetime.fromtimestamp(int(os.path.getmtime(log_file_name)))
        else:
            return "unknown"
    else:
        if os.path.isfile(log_file_name + ".0"):
            return datetime.datetime.fromtimestamp(int(os.path.getmtime(log_file_name + ".0")))
        else:
            return "unknown"

def printTableHead():
    print "<p><span id='update-time'>", "Update time: ",str(datetime.datetime.fromtimestamp(int(time.time()))), "</span></p>"
    print "<table class='tbl-status'><thead><tr>"
    print "<th>Archive name</th>"
    print "<th>Sync status</th>"
    print "<th>Sync time</th>"
    print "<th>Exit status</th>"
    print "<th>Upstream</th>"
    print "<th>Size</th>"
    print "</tr></thead><tbody>"

def printTableTail():
    print "</tbody></table>"

if __name__ == "__main__":
    printTableHead()

    mirrors = open(os.path.join(ETC_BASE, "mirrors.json"))
    repo_list = json.load(mirrors)

    for repo in repo_list:
        name = '<a href="/{0}/">{1}</a>'.format(repo["repo_path"], repo["repo_name"])

        if "log_path" in repo.keys() and "script_type" in repo.keys():
            log_filename = getLogFileName(repo["log_path"], repo["script_type"])
        else:
            log_filename = ""

        status = getSyncStatus(log_filename)
        _has_error, size, size_in_byte = getSyncErrorAndArchiveSize(log_filename)
        status_format = '{0}{1}{2}'.format("<td class='td-archive-" + status + "'>", status, HTML_TAGS["end_td"])

        exit_status = "unknown" if status == "running" or status == "unknown" else \
                "fail" if _has_error else "success"
        exit_status_format = '{0}{1}{2}'.format("<td class='td-archive-" + exit_status + "'>", exit_status, HTML_TAGS["end_td"])

        size_format = '{0}{1}{2}{3}{4}{5}'.format(HTML_TAGS["begin_td"], size, "<p style='display:none'>", size_in_byte, "</p>", HTML_TAGS["end_td"])

        if "upstream" in repo.keys():
            upstream = repo["upstream"]
        else:
            try:
                upstream = getArchiveUpstream(repo["log_path"], repo["script_type"])
            except KeyError:
                upstream = "unknown"
            except IOError:
                continue

        if "sync_time" in repo.keys():
            time = repo["sync_time"]
        else:
            time = getArchiveSyncTime(log_filename, status)
        time_format = '{0}{1}{2}'.format(HTML_TAGS["begin_td"], time, HTML_TAGS["end_td"])

        print HTML_TAGS["begin_tr"], \
                HTML_TAGS["begin_td"], name, HTML_TAGS["end_td"], \
                status_format, \
                time_format, \
                exit_status_format, \
                HTML_TAGS["begin_td"], upstream, HTML_TAGS["end_td"], \
                size_format, \
                HTML_TAGS["end_tr"]

    printTableTail()

