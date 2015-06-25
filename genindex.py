#!/usr/bin/python3 -O
# -*- coding: utf-8 -*-

from jinja2 import Environment, FileSystemLoader
import gencontent
import genisolist

OUTFILE = os.path.join(gencontent.HTTPDIR, 'index.html')
env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('index.html')
parsed_template = template.render(
        repolist=gencontent.genRepoList(), 
        isoinfo=genisolist.getImageList() )

with open(OUTFILE,'w') as fout:
    fout.write(parsed_template)
    fout.write('\n')

