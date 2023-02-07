#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml
import xml.dom
import xml.dom.minidom
import requests
import signal
import utils
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

    logger = glob_logger if glob_logger else logging.getLogger()

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
    try:
        resp = utils.get_resp_with_timeout(SERVERNEWS_FEED, logger=logger)
        if resp is None:
            # failed
            return newslist
        newslist = list(parseFeedData(resp.text))
        logger.info('newslist generation successful, size is {}.'.format(len(newslist)))
    except Exception as e:
        logger.error('unknown exception caught: "{}".'.format(str(e)))
    finally:
        return newslist

if __name__ == "__main__":
    for i in getServerNews():
        print(i.title, i.link)

#  vim: set ts=8 sw=4 tw=0 et :
