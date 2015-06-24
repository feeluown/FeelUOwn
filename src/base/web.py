# -*- coding:utf8 -*-

from PyQt5.QtCore import QObject, pyqtSignal
import urllib
import http.cookiejar

from base.logger import LOG
from base.common import singleton


@singleton
class MyWeb(QObject):
    """simulate a web browser
    the simulated brower has two method: get and post.
    """
    signal_load_progress = pyqtSignal([int])

    def __init__(self):
        super().__init__()
        self.header = {
            'Host': 'music.163.com',
            'Connection': 'keep-alive',
            'cache-control': 'private',
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
            'Referer': 'http://music.163.com/song?id=26599525',
            "User-Agent": "Opera/8.0 (Macintosh; PPC Mac OS X; U; en)"
        }
        self.cookie = http.cookiejar.LWPCookieJar()
        self.cookie_support = urllib.request.HTTPCookieProcessor(self.cookie)
        self.opener = urllib.request.build_opener(self.cookie_support,
                                                  urllib.request.HTTPHandler)
        self.timeout = 1
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
            response = urllib.request.urlopen(request)
            res = self.show_progress(response)
            return res
        except Exception as e:
            LOG.error(str(e))
            return {'code': 408}

    def get(self, url):
        """Load data from the server using a HTTP GET request.

        :param url: the URL to which the request is sent.
        :return content: return HTTPResponse Objects, generally speaking, we use READ method.
        """
        request = urllib.request.Request(url, None, self.header)
        try:
            response = urllib.request.urlopen(request)
            return self.show_progress(response)
        except Exception as e:
            LOG.error(str(e))
            return {'code': 408}

    def show_progress(self, response):
        content = bytes()
        try:
            total_size = response.getheader('Content-Length').strip()
        except:
            LOG.info(u'这个网络response没有Content-Length字段')
            return response.read()
        chunk_size = 8192
        total_size = int(total_size)
        bytes_so_far = 0

        while 1:
            chunk = response.read(chunk_size)
            content += chunk
            bytes_so_far += len(chunk)
            progress = round(bytes_so_far * 1.0 / total_size * 100)
            self.signal_load_progress.emit(progress)
            if not chunk:
                break
        return content