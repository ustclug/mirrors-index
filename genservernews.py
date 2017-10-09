#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml
import xml.dom
import xml.dom.minidom
import requests
import signal
import syslog
import logging

"""
Generate HTML Fragment about latest server news.
"""

SERVERNEWS_FEED = "https://servers.ustclug.org/category/mirrors/feed/"
SERVERNEWS_MAX_NUM = 3


def getServerNews(glob_logger: logging.Logger = None) -> list:
    """
    return list of NewRecord object.

    Timeout is set to 20 seconds.
    """

    logger = glob_logger if glob_logger else logger.getLogger()

    class AlarmTimeoutException(Exception):
        pass

    class BadRequestException(Exception):
        pass

    def alarm_handler(signum, frame):
        raise AlarmTimeoutException

    def parseFeedData(text):
        """
        Will return proper HTML String by input.
        """
        class NewsRecord():
            def __init__(self, item):
                """Only The most useful data are picked for now."""
                self.title = item.getElementsByTagName('title')[0].firstChild.nodeValue
                self.link = item.getElementsByTagName('link')[0].firstChild.nodeValue

        # impl = xml.dom.getDOMImplementation() # Not needed in parsing
        doc = xml.dom.minidom.parseString(text)

        for item in doc.getElementsByTagName('item')[:SERVERNEWS_MAX_NUM]:
            yield NewsRecord(item)

    logger.info('begin generation of ServerNews...')
    newslist = []
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(20)
    try:
        page = requests.get(SERVERNEWS_FEED)
        if page.status_code != 200:
            raise BadRequestException
        newslist = list(parseFeedData(page.text))
    except AlarmTimeoutException:
        logger.error('generation of ServerNews timed out')
    except BadRequestException:
        logger.error('failed to retrieve data from servers.blog')
    except Exception as e:
        logger.error('unknown exception caught: "{}".'.format(str(e)))
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        logger.info('newslist generation successful, size is {}.'.format(len(newslist)))
        return newslist

if __name__ == "__main__":
    for i in getServerNews():
        print(i.title, i.link)

#  vim: set ts=8 sw=4 tw=0 et :
