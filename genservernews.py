#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml
import xml.dom
import xml.dom.minidom
import jinja2
import requests
import signal
import syslog

"""
Generate HTML Fragment about latest server news.
"""

SERVERNEWS_FEED = "https://servers.blog.ustc.edu.cn/category/mirrors/feed/"
SERVERNEWS_MAX_NUM = 3
# Use Jinja2 Template? add to template doc
SERVERNEWS_TEMPLATE = """\
        <h3>镜像站新闻通知</h3>
{% for record in newslist %}
        <p><a href="{{ record.link }}">{{ record.title }}</a></p>
{% endfor %}
"""

def getServerNews():
    """
    return HTML String containing Server News information.

    Timeout is set to 20 seconds.
    """

    servernews=""
    error_log="Mirrors-indexgen: {0}, ignoring."

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
                pass

        htmldata = ""

        # impl = xml.dom.getDOMImplementation() # Not needed in parsing
        doc = xml.dom.minidom.parseString(request.text)
        counter = 0
        newslist = []
        for item in doc.getElementsByTagName('item'):
            counter += 1
            record = NewsRecord(item)
            newslist.append(record)
            if counter >= SERVERNEWS_MAX_NUM:
                break

        template = jinja2.Template(SERVERNEWS_TEMPLATE)
        htmldata = template.render(newslist=newslist)
        return htmldata

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(20)
    try:
        request = requests.get(SERVERNEWS_FEED)
        if request.status_code != 200:
            raise BadRequestException
        servernews = parseFeedData(request.text)
    except AlarmTimeoutException:
        syslog.syslog(syslog.LOG_ERR, error_log.format('generating ServerNews timed out'))
    except BadRequestException:
        syslog.syslog(syslog.LOG_ERR, error_log.format('failed to retrieve data from servers.blog'))
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, error_log.format('unknown Exception happened:{}'.format(e.__str__())))
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
    
    return servernews

# DEBUG
if __name__ == "__main__":
    print(getServerNews())

#  vim: set ts=8 sw=4 tw=0 et :
