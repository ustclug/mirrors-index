#!/usr/bin/python

import os, time, os.path

h=open('/home/mirror/newindex/header.html','r')
output=h.read()
h.close()

dir = '/srv/www/'

output+='<table cellpadding="0" cellspacing="0" class="filelist">\n'
output+='<thead><tr id="firstline"><th id="name">Folder</th><th>Last Update</th><th id="help">Help</th></tr></thead>\n'
for file in sorted(os.listdir(dir)):
	if file[0] != '.' and not file.endswith('.html') and file != 'tmpfs':
                logdir=('/home/mirror/log/'+file).lower()
                if file == 'sourceware.org': logdir='/home/mirror/log/cygwin/'
                if file == 'scientificlinux': logdir='/home/mirror/log/scientific/'
                if file == 'progress-linux': logdir='/home/mirror/log/progress/'
                if file == 'uksm-kernel': logdir='/home/mirror/log/uksm/'
                if file == 'fedora': logdir='/home/mirror/log/fedora-linux/'
                if file == 'kde-applicationdata': logdir='/home/mirror/log/kde-application/'
                try:
                    modtime=time.strftime('%Y-%m-%d %H:%I:%S', time.localtime(os.path.getmtime(logdir)))
                except os.error:
                    modtime=time.strftime('%Y-%m-%d %H:%I:%S', time.localtime(os.path.getmtime(dir+file)))
		output+='<tr><td class="filename"><a href="/'+file+'">'+file+'</a></td><td class="filetime">'+modtime+'</td><td class="help"><a href="help/'+file+'">Help</a></td></tr>\n'
output+='</table>'
m=open('/home/mirror/newindex/middle.html','r')
output+=m.read()
m.close
info=open('/home/mirror/newindex/isoinfo.json','r')
output+=info.read()
info.close
f=open('/home/mirror/newindex/footer.html','r')
output+=f.read()
f.close()
w=open('/srv/www/index.html','w')
w.write(output)
w.close()
