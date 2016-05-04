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
    logger = logging.getLogger('mirrors-genindex')
    ch = logging.StreamHandler()
    OUTDIR = os.getenv('HTTPDIR') or gencontent.HTTPDIR
    parser = argparse.ArgumentParser(
            description="USTC Mirrors Index Page Generator",
            epilog="Brought to you by LUG@USTC.")
    parser.add_argument(
            '-d', '--outdir',
            type=str,
            default=OUTDIR,
            help='specify output directory',
            )
    parser.add_argument(
            '-o', '--output',
            type=str,
            default=os.path.join(OUTDIR, 'index.html'),
            help='specify full output file path, and will overwrite outdir option',
            )
    parser.add_argument(
            '-v', '--verbose',
            help='show verbose information',
            action='store_true',
            )
    args = parser.parse_args()
    LOGLEVEL = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(LOGLEVEL)
    ch.setLevel(LOGLEVEL)
    ch.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
    logger.addHandler(ch)
    logger.debug('received command arguments: "{}"'.format(str(args)))
    OUTDIR = args.outdir or OUTDIR
    OUTFILE = args.output
    BASEDIR = os.path.dirname(__file__)
    logger.info('OUTFILE is "%(OUTFILE)s"' % locals())
    logger.info('BASEDIR is "%(BASEDIR)s"' % locals())
    env = Environment(loader=FileSystemLoader(os.path.join(BASEDIR, 'templates')))
    template = env.get_template('index.html')
    logger.debug('begin parsing template...')
    parsed_template = template.render(
            repolist=gencontent.genRepoList(),
            revproxy=gencontent.getOthers(),
            isoinfo=genisolist.getImageList(),
            newslist=genservernews.getServerNews(logger))

    logger.info('begin file writing...')
    with open(OUTFILE, 'w') as fout:
        fout.write(parsed_template)
        fout.write(os.linesep)
    logger.info('completed! exiting...')

if __name__ == "__main__":
    main()

