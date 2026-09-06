#!/usr/bin/env python3

import argparse
import copy
import json
import logging
import os
import tempfile
import time

from jinja2 import Environment, FileSystemLoader, select_autoescape

import gencontent
import genservernews
from utils import get_isolist

BASEDIR = os.path.dirname(__file__)
with open(os.path.join(BASEDIR, "config", "genmirrorz.json")) as source:
    descriptions = json.load(source).get("descriptions", {})
    descriptions_by_name = {
        name.lower(): description for name, description in descriptions.items()
    }


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


def index_json(repolist, revproxy, isoinfo, newslist, generated_at):
    data = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "repositories": [
            {
                "updatedAt": updated_at,
                "helpUrl": help_url,
                "name": name,
                "desc": descriptions_by_name.get(name.lower(), ""),
            }
            for updated_at, help_url, _help_text, name in repolist
        ],
        "reverseProxies": [
            {"source": source, "destination": destination}
            for source, destination in revproxy
        ],
        "downloads": isoinfo,
        "news": [{"title": record.title, "url": record.link} for record in newslist],
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def httpdir_exists(path):
    return os.path.exists(path)


def main():
    logger = logging.getLogger("mirrors-genindex")
    ch = logging.StreamHandler()
    OUTDIR = os.getenv("OUTDIR") or gencontent.OUTDIR
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
        "-v",
        "--verbose",
        help="show verbose information",
        action="store_true",
    )
    args = parser.parse_args()

    if not args.outdir:
        parser.error("--outdir is required when OUTDIR is not configured")

    LOGLEVEL = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(LOGLEVEL)
    ch.setLevel(LOGLEVEL)
    ch.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logger.addHandler(ch)
    logger.debug(f'received command arguments: "{args!s}"')

    OUTDIR = args.outdir or OUTDIR
    index_file = os.path.join(OUTDIR, "static", "json", "index.json")
    nojs_file = os.path.join(OUTDIR, "index-nojs.html")
    mirrorz_file = os.path.join(OUTDIR, "static", "json", "mirrorz.json")
    logger.info(f'OUTDIR is "{OUTDIR}"')
    logger.info(f'BASEDIR is "{BASEDIR}"')
    if not httpdir_exists(gencontent.HTTPDIR):
        logger.warning(
            'HTTPDIR "%s" does not exist; continuing without filesystem discovery',
            gencontent.HTTPDIR,
        )
    env = Environment(
        loader=FileSystemLoader(os.path.join(BASEDIR, "templates")),
        autoescape=select_autoescape(["html"]),
    )
    nojs_template = env.get_template("index-nojs.html")

    snapshots = gencontent.fetch_yuki_metadata()
    homepage_meta = gencontent.metadata_for(snapshots, "homepage")
    mirrorz_meta = gencontent.metadata_for(snapshots, "mirrorz")

    import genmirrorz

    genmirrorz.collect_repo_contributions(mirrorz_meta)
    repolist = list(gencontent.genRepoList(homepage_meta))
    revproxy = list(gencontent.getOthers())
    isoinfo = get_isolist()
    newslist = genservernews.getServerNews(logger)
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    failures = []

    def generate(label, path, producer):
        logger.info(f'begin {label} writing to "{path}"...')
        try:
            atomic_write(path, producer())
        except Exception as error:
            failures.append((label, error))
            logger.exception(f"failed to generate {label}")
        else:
            logger.info(f"{label} completed!")

    generate(
        "index.json",
        index_file,
        lambda: index_json(repolist, revproxy, isoinfo, newslist, now),
    )
    generate(
        "index-nojs.html",
        nojs_file,
        lambda: nojs_template.render(
            repolist=repolist,
            descriptions_by_name=descriptions_by_name,
            now=now,
        ),
    )

    def make_mirrorz():
        return genmirrorz.getMirrorzJson(
            repolist, copy.deepcopy(isoinfo), meta=mirrorz_meta
        )

    generate("mirrorz.json", mirrorz_file, make_mirrorz)

    if failures:
        logger.error(
            "generation completed with failures: %s",
            ", ".join(label for label, _error in failures),
        )
        raise SystemExit(1)

    logger.info("exiting...")


if __name__ == "__main__":
    main()
