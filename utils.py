import signal
from typing import Optional
from genisolist import process_ini, gen_from_sections
import requests
import logging
import os
import json
import functools
from pathlib import Path

logger = logging.getLogger(__name__)
CONFIG_FOLDER = Path(os.path.dirname(__file__)) / "config"


class AlarmTimeoutException(Exception):
    pass


class BadRequestException(Exception):
    pass


def alarm_handler(signum, frame):
    raise AlarmTimeoutException


# return None when exception caught
def get_resp_with_timeout(
    url: str, timeout: int = 20, logger: logging.Logger = None
) -> Optional[requests.Response]:
    if logger is None:
        logger = logging.getLogger()
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            raise BadRequestException
        return resp
    except AlarmTimeoutException:
        logger.error(f"requesting {url} timed out")
    except BadRequestException:
        logger.error(f"failed to retrieve data from {url}")
    except Exception as e:
        logger.error('unknown exception caught: "{}".'.format(str(e)))
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
    return None


# Currently within one run, we expect to download cname.json only once.
@functools.cache
def get_mirrorz_cname():
    cname_path = CONFIG_FOLDER / "cname.json"
    # download cname
    try:
        req = requests.get("https://mirrorz.org/static/json/cname.json", timeout=10)
        req.raise_for_status()
        cname = req.json()
        with open(cname_path, "w") as f:
            json.dump(cname, f)
    except:
        # website req timeout, use local cname
        try:
            logger.warn("Failed to fetch mirrorz cname.json, try using local one")
            with open(cname_path) as f:
                cname = json.load(f)
        except:
            logger.warn("Failed to load mirrorz cname.json")
            cname = {}
    return cname


# Used by multiple generators, to directly use reference impl without modification
def get_isolist():
    genisolist_inifile = CONFIG_FOLDER / "genisolist.ini"
    sections = process_ini(genisolist_inifile)
    return gen_from_sections(sections)
