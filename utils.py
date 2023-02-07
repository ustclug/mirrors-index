import signal
from typing import Optional
import requests
import logging

class AlarmTimeoutException(Exception):
    pass

class BadRequestException(Exception):
    pass

def alarm_handler(signum, frame):
    raise AlarmTimeoutException

# return None when exception caught
def get_resp_with_timeout(url: str, timeout: int = 20, logger: logging.Logger = None) -> Optional[requests.Response]:
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
        logger.error(f'requesting {url} timed out')
    except BadRequestException:
        logger.error('failed to retrieve data from {url}')
    except Exception as e:
        logger.error('unknown exception caught: "{}".'.format(str(e)))
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
    return None
