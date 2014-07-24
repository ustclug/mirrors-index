#!/usr/bin/python

import os, time, os.path
from get_mirror_status import *
import json
import genisolist

homedir='/home/mirror/'
basedir='/home/mirror/newindex/' # must has a '/' in the end
serverdir = '/srv/www/'

h=open(basedir+'header.html','r')
output=h.read()
h.close()

mirrors = open(homedir+'etc/mirrors.json')
repo_list = json.load(mirrors)

def getRepoInfo(repo_name) :
        for repo in repo_list:
                if repo.get('log_path', '') == repo_name:
                        return repo

        return None

output+='<table cellpadding="0" cellspacing="0" class="filelist">\n'
output+='<thead><tr id="firstline"><th id="name">Folder</th><th>Last Update</th><th id="help">Help</th></tr></thead>\n'
for file in sorted(os.listdir(serverdir)):
        if file[0] != '.' and not file.endswith('.html') and file != 'tmpfs':
                _file = file    # a wrapper for the real log file name
                if file == 'sourceware.org':
                        _file = 'cygwinports'
                if file == 'scientificlinux':
                        _file = 'scientific'
                if file == 'progress-linux':
                        _file = 'progress'
                if file == 'uksm-kernel':
                        _file = 'uksm'
                if file == 'fedora':
                        _file = 'fedora-linux'
                if file == 'kde-applicationdata':
                        _file = 'kde-application'
                if file == 'bioc':
                        _file = 'bioc_2_13'
                if file == 'archive.raspberrypi.org':
                        _file = 'raspberrypi'
                if file == 'kernel.org':
                        _file = 'kernelorg'
                logdir=(homedir+'log/'+_file).lower()
                # try:
                #         modtime=time.strftime('%Y-%m-%d %H:%I:%S', time.localtime(os.path.getmtime(logdir)))
                # except os.error:
                #         modtime=time.strftime('%Y-%m-%d %H:%I:%S', time.localtime(os.path.getmtime(dir+file)))
                repo_info = getRepoInfo(_file.lower())
                if repo_info is not None:
                        log_filename = getLogFileName(repo_info['log_path'], repo_info.get('script_type', ''))
                        status = getSyncStatus(log_filename)
                        if "sync_time" in repo_info.keys():
                                modtime = repo_info["sync_time"]
                        else:
                                modtime = getArchiveSyncTime(log_filename, status).strftime("%Y-%m-%d %H:%M:%S")
                else:
                        modtime = 'Not Syncing'
                output+='<tr><td class="filename"><a href="/'+file+'">'+file+'</a></td><td class="filetime">'+str(modtime)+'</td><td class="help"><a href="help/'+file+'">Help</a></td></tr>\n'

output+='</table>'
m=open(basedir+'middle.html','r')
output+=m.read()
m.close()

#info=open(basedir+'isoinfo.json','r')
#output+=info.read()
#info.close()
output += genisolist.getImageList()

f=open(basedir+'footer.html','r')
output+=f.read()
f.close()
w=open(serverdir+'index.html','w')
w.write(output)
w.close()
