#!/usr/bin/env python3

import argparse
import json
import logging
import os
import tempfile
import time

from jinja2 import Environment, FileSystemLoader, select_autoescape

import gencontent
import genservernews
from utils import get_isolist


def atomic_write(path, content):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".mirrors-index-", dir=directory, text=True)
    try:
        with os.fdopen(fd, "w") as output:
            output.write(content)
            output.write(os.linesep)
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def bootstrap_json(repolist, revproxy, isoinfo, newslist, generated_at):
    data = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "repositories": [
            {"updatedAt": updated_at, "helpUrl": help_url, "name": name}
            for updated_at, help_url, _help_text, name in repolist
        ],
        "reverseProxies": [
            {"source": source, "destination": destination}
            for source, destination in revproxy
        ],
        "downloads": isoinfo,
        "news": [{"title": record.title, "url": record.link} for record in newslist],
    }
    return (
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def frontend_asset(name, base_directory=None):
    base_directory = base_directory or os.path.dirname(__file__)
    manifest_path = os.getenv("FRONTEND_MANIFEST") or os.path.join(
        base_directory, "dist", "manifest.json"
    )
    try:
        with open(manifest_path) as source:
            manifest = json.load(source)
        asset = manifest[name]
        if not isinstance(asset, str) or not asset.startswith("/static/"):
            raise ValueError("invalid asset path")
        return asset
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f'Frontend assets are not built; invalid manifest "{manifest_path}"'
        ) from error


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
    logger.debug(f'received command arguments: "{args!s}"')

    OUTDIR = args.outdir or OUTDIR
    OUTFILE = args.output
    BASEDIR = os.path.dirname(__file__)
    logger.info(f'OUTFILE is "{OUTFILE}"')
    logger.info(f'BASEDIR is "{BASEDIR}"')
    env = Environment(
        loader=FileSystemLoader(os.path.join(BASEDIR, "templates")),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("index.html")
    nojs_template = env.get_template("index-nojs.html")
    logger.debug("begin parsing template...")

    repolist = list(gencontent.genRepoList())
    revproxy = list(gencontent.getOthers())
    isoinfo = get_isolist()
    newslist = genservernews.getServerNews(logger)
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    parsed_template = template.render(
        repolist=repolist,
        bootstrap=bootstrap_json(repolist, revproxy, isoinfo, newslist, now),
        index_script=frontend_asset("index", BASEDIR),
        index_style=frontend_asset("index_style", BASEDIR),
        now=now,
    )
    parsed_nojs_template = nojs_template.render(
        repolist=repolist,
        nojs_style=frontend_asset("nojs_style", BASEDIR),
        now=now,
    )

    nojs_file = os.path.join(
        os.path.dirname(os.path.abspath(OUTFILE)), "index-nojs.html"
    )
    logger.info(f'begin no-JavaScript index file writing to "{nojs_file}"...')
    atomic_write(nojs_file, parsed_nojs_template)
    logger.info("no-JavaScript index file completed!")

    logger.info("begin index file writing...")
    atomic_write(OUTFILE, parsed_template)
    logger.info("index file completed!")

    if args.mirrorz:
        # Put genmirrorz inside genindex to save time and I/O generating files
        import genmirrorz

        logger.info("begin mirrorz.json file writing...")
        atomic_write(args.mirrorz, genmirrorz.getMirrorzJson(repolist, isoinfo))
        logger.info("mirrorz.json file completed!")

    logger.info("exiting...")


if __name__ == "__main__":
    main()
