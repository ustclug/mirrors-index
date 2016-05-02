#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import argparse
from jinja2 import Environment, FileSystemLoader
import gencontent
import genisolist
import genservernews

def main():
    parser = argparse.ArgumentParser(
            description="USTC Mirrors Index Page Generator",
            epilog="Brought to you by LUG@USTC.")
    parser.add_argument(
            '-o', '--output',
            type=str,
            default=os.path.join(gencontent.HTTPDIR, 'index.html'),
            help='specify output html file',
            )
    args = parser.parse_args()
    OUTFILE = args.output
    BASEDIR = os.path.dirname(__file__)
    env = Environment(loader=FileSystemLoader(os.path.join(BASEDIR, 'templates')))
    template = env.get_template('index.html')
    parsed_template = template.render(
            repolist=gencontent.genRepoList(),
            revproxy=gencontent.getOthers(),
            isoinfo=genisolist.getImageList(),
            newslist=genservernews.getServerNews())

    with open(OUTFILE, 'w') as fout:
        fout.write(parsed_template)
        fout.write(os.linesep)

if __name__ == "__main__":
    main()

