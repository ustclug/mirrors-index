#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from jinja2 import Environment, FileSystemLoader
import gencontent
import genisolist
import genservernews

OUTFILE = os.path.join(gencontent.HTTPDIR, 'index.html')
BASEDIR = os.path.dirname(__file__)
env = Environment(loader=FileSystemLoader(os.path.join(BASEDIR, 'templates')))
template = env.get_template('index.html')
parsed_template = template.render(
        repolist=gencontent.genRepoList(),
        isoinfo=genisolist.getImageList(),
        newslist=genservernews.getServerNews())

with open(OUTFILE, 'w') as fout:
    fout.write(parsed_template)
    fout.write(os.linesep)

