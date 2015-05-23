# -*- coding:utf8 -*-

import urllib.request, urllib.parse, urllib.error
import http.cookiejar

from src.base.logger import LOG
from src.base.common import singleton


@singleton
class MyWeb():
    """simulate a web browser
    the simulated brower has two method: get and post.
    """
    def __init__(self):
        self.header = {
            'Host': 'music.163.com',
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
            'Referer': 'http://music.163.com/song?id=26599525',
            "User-Agent": "Opera/8.0 (Macintosh; PPC Mac OS X; U; en)"
        }
        self.cookie = http.cookiejar.LWPCookieJar()
        self.cookie_support = urllib.request.HTTPCookieProcessor(self.cookie)
        self.opener = urllib.request.build_opener(self.cookie_support,
                                                  urllib.request.HTTPHandler)
        urllib.request.install_opener(self.opener)

    def post(self, posturl, dictdata):
        """Load data from the server using a HTTP POST request.

        :param string posturl: the URL to which the request is sent.
        :param dict dictdata: a dict object that is sent to the server with the request.
        """

        postdata = urllib.parse.urlencode(dictdata)
        postdata = postdata.encode('utf-8')
        request = urllib.request.Request(posturl, postdata, self.header)
        try:
            content = urllib.request.urlopen(request)
            return content
        except Exception as e:
            LOG.warning(str(e))
            return None

    def get(self, url):
        """Load data from the server using a HTTP GET request.

        :param url: the URL to which the request is sent.
        :return content: return HTTPResponse Objects, generally speaking, we use READ method.
        """
        request = urllib.request.Request(url, None, self.header)
        try:
            content = urllib.request.urlopen(request)
            return content
        except Exception as e:
            LOG.warning(str(e))
            return None