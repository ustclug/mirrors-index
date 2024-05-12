#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import argparse
from jinja2 import Environment, FileSystemLoader
import time

import gencontent
from utils import get_isolist
import genservernews


def main():
    logger = logging.getLogger("mirrors-genindex")
    ch = logging.StreamHandler()
    OUTDIR = (
        os.getenv("OUTDIR")
        or gencontent.OUTDIR
        or os.getenv("HTTPDIR")
        or gencontent.HTTPDIR
    )
    parser = argparse.ArgumentParser(
        description="USTC Mirrors Index Page Generator",
        epilog="Brought to you by LUG@USTC.",
    )
    parser.add_argument(
        "-d",
        "--outdir",
        type=str,
        default=OUTDIR,
        help="specify output directory",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=os.path.join(OUTDIR, "index.html"),
        help="specify full output file path, and will overwrite outdir option",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="show verbose information",
        action="store_true",
    )
    parser.add_argument(
        "-m",
        "--mirrorz",
        type=str,
        default=None,
        help="set mirrorz output file path, mirrorz.json will not be generated if not set",
    )
    args = parser.parse_args()

    LOGLEVEL = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(LOGLEVEL)
    ch.setLevel(LOGLEVEL)
    ch.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logger.addHandler(ch)
    logger.debug('received command arguments: "{}"'.format(str(args)))

    OUTDIR = args.outdir or OUTDIR
    OUTFILE = args.output
    BASEDIR = os.path.dirname(__file__)
    logger.info('OUTFILE is "%(OUTFILE)s"' % locals())
    logger.info('BASEDIR is "%(BASEDIR)s"' % locals())
    env = Environment(loader=FileSystemLoader(os.path.join(BASEDIR, "templates")))
    template = env.get_template("index.html")
    logger.debug("begin parsing template...")

    repolist = list(gencontent.genRepoList())
    revproxy = gencontent.getOthers()
    isoinfo = get_isolist()
    newslist = genservernews.getServerNews(logger)

    parsed_template = template.render(
        repolist=repolist,
        revproxy=revproxy,
        isoinfo=isoinfo,
        newslist=newslist,
        now=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    )

    logger.info("begin index file writing...")
    with open(OUTFILE, "w") as fout:
        fout.write(parsed_template)
        fout.write(os.linesep)
    logger.info("index file completed!")

    if args.mirrorz:
        # Put genmirrorz inside genindex to save time and I/O generating files
        import genmirrorz

        logger.info("begin mirrorz.json file writing...")
        with open(args.mirrorz, "w") as fout:
            fout.write(genmirrorz.getMirrorzJson(repolist, isoinfo))
            fout.write(os.linesep)
        logger.info("mirrorz.json file completed!")

    logger.info("exiting...")


if __name__ == "__main__":
    main()
