import functools
import json
import logging
import os
import signal
import tempfile
from pathlib import Path

import requests

from genisolist import gen_from_sections, process_ini

logger = logging.getLogger(__name__)
BUNDLED_CONFIG = Path(__file__).parent / "config"
CONFIG_FOLDER = Path(os.environ.get("MIRRORS_CONFIG_DIR", BUNDLED_CONFIG))


class AlarmTimeoutError(Exception):
    pass


class BadRequestError(Exception):
    pass


def alarm_handler(signum, frame):
    raise AlarmTimeoutError


# return None when exception caught
def get_resp_with_timeout(
    url: str, timeout: int = 20, logger: logging.Logger | None = None
) -> requests.Response | None:
    if logger is None:
        logger = logging.getLogger()
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            raise BadRequestError
        return resp
    except AlarmTimeoutError:
        logger.error(f"requesting {url} timed out")
    except BadRequestError:
        logger.error(f"failed to retrieve data from {url}")
    except requests.RequestException as e:
        logger.error(f'unknown exception caught: "{e!s}".')
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
    return None


# Currently within one run, we expect to download cname.json only once.
@functools.cache
def get_mirrorz_cname(upstream: str | None = None):
    cname_path = CONFIG_FOLDER / "cname.json"
    url = upstream or "https://mirrors.cernet.edu.cn/static/json/cname.json"
    try:
        req = requests.get(url, timeout=10)
        req.raise_for_status()
        cname = req.json()
    except (OSError, ValueError, requests.RequestException):
        logger.warning("Failed to fetch MirrorZ canonical names")
        for path in (cname_path, BUNDLED_CONFIG / "cname.json"):
            try:
                with path.open() as source:
                    return json.load(source)
            except (OSError, ValueError):
                continue
        return {}
    if CONFIG_FOLDER == BUNDLED_CONFIG:
        try:
            atomic_write(cname_path, json.dumps(cname))
        except OSError:
            logger.warning("Could not cache MirrorZ canonical names")
    return cname


# Used by multiple generators, to directly use reference impl without modification
def get_isolist():
    genisolist_inifile = CONFIG_FOLDER / "genisolist.ini"
    sections = process_ini(genisolist_inifile)
    return gen_from_sections(sections)


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
