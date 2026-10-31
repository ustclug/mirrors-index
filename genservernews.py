#!/usr/bin/env python3

import datetime
import logging
import os
import re
import xml
import xml.dom
import xml.dom.minidom
from xml.parsers.expat import ExpatError

import utils
from siteconfig import SITE

"""
Generate HTML Fragment about latest server news.
"""

SERVERNEWS_FEED = "https://servers.ustclug.org/feed/mirrors.xml"
SERVERNEWS_MAX_NUM = 3


def getServerNews(glob_logger: logging.Logger | None = None) -> list:
    """
    return list of NewsRecord object.

    Timeout is set to 20 seconds.
    """

    logger = glob_logger or logging.getLogger()

    def parseFeedData(text):
        """
        Will return proper HTML String by input.
        """

        class NewsRecord:
            def __init__(self, item):
                """Only The most useful data are picked for now."""
                self.title = item.getElementsByTagName("title")[0].firstChild.nodeValue
                self.link = item.getElementsByTagName("link")[0].getAttribute("href")
                self.date = datetime.datetime.fromisoformat(
                    item.getElementsByTagName("published")[0].firstChild.nodeValue
                )
                self.date_str = self.date.strftime("%Y-%m-%d")

                # if title does not already ends with a date marker
                if not re.search(r" \(\d{4}-\d{2}-\d{2}\)$", self.title):
                    self.title += f" ({self.date_str})"

        # impl = xml.dom.getDOMImplementation() # Not needed in parsing
        doc = xml.dom.minidom.parseString(text)
        current_num = 0
        for item in doc.getElementsByTagName("entry"):
            if current_num >= SERVERNEWS_MAX_NUM:
                break
            category = (
                SITE.get("newsCategory", "")
                if SITE
                else os.environ.get("NEWS_CATEGORY", "mirrors")
            )
            if category and not any(
                node.getAttribute("term") == category
                for node in item.getElementsByTagName("category")
            ):
                continue
            current_num += 1
            yield NewsRecord(item)

    feed = (
        SITE.get("newsFeed", "")
        if SITE
        else os.environ.get("NEWS_FEED", SERVERNEWS_FEED)
    )
    if not feed:
        return []
    logger.info("begin generation of ServerNews...")
    newslist = []
    try:
        resp = utils.get_resp_with_timeout(feed, logger=logger)
        if resp is None:
            # failed
            return newslist
        newslist = list(parseFeedData(resp.text))
        logger.info(f"newslist generation successful, size is {len(newslist)}.")
    except (AttributeError, ExpatError, IndexError, ValueError) as e:
        logger.error(f'unknown exception caught: "{e!s}".')
    return newslist


if __name__ == "__main__":
    for i in getServerNews():
        print(i.title, i.link)

# vim:set ts=8 sw=4 tw=0 et:
