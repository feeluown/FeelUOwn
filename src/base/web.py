# -*- coding:utf8 -*-

import requests
import json
import pickle

from PyQt5.QtCore import QObject, pyqtSignal

from base.logger import LOG
from base.common import singleton, func_coroutine
from constants import DATA_PATH


@singleton
class MyWeb(QObject):
    """simulate a web browser
    the simulated brower has two method: get and post.
    """
    signal_load_progress = pyqtSignal([int])

    def __init__(self):
        super().__init__()
        self.headers = {
            'Host': 'music.163.com',
            'Connection': 'keep-alive',
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
            'Referer': 'http://music.163.com/',
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36"
        }

        self.cookies = dict(appver="1.2.1", os="osx")

    def post(self, url, data):
        """Load data from the server using a HTTP POST request.

        :param string posturl: the URL to which the request is sent.
        :param dict dictdata: a dict object that is sent to the server with the request.
        """


        try:
            res = requests.post(url, data=data, headers=self.headers, cookies=self.cookies)
            content = self.show_progress(res)
            return content
        except Exception as e:
            LOG.error(str(e))
            return b'{"code": 408}'

    def post_and_updatecookies(self, url, data):
        try:
            res = requests.post(url, data=data, headers=self.headers, cookies=self.cookies)
            self.cookies.update(res.cookies.get_dict())
            requests.session().cookies = self.cookies
            self.save_cookies()
            return res.json()
        except Exception as e:
            LOG.error(str(e))
            return b'{"code": 408}'

    def get(self, url):
        """Load data from the server using a HTTP GET request.

        :param url: the URL to which the request is sent.
        :return content: return HTTPResponse Objects, generally speaking, we use READ method.
        """
        try:
            res = requests.get(url, headers=self.headers)
            content = self.show_progress(res)
            return content
        except Exception as e:
            LOG.error(str(e))
            return b'{"code": 408}'

    def show_progress(self, response):
        content = bytes()
        total_size = response.headers.get('content-length')
        if total_size is None:
            LOG.info(u'这个网络response没有Content-Length字段')
            content = response.content
            return content
        else:
            total_size = int(total_size)
            bytes_so_far = 0

            for chunk in response.iter_content():
                content += chunk
                bytes_so_far += len(chunk)
                progress = round(bytes_so_far * 1.0 / total_size * 100)
                self.signal_load_progress.emit(progress)
            return content

    @func_coroutine
    def save_cookies(self):
        try:
            with open(DATA_PATH + "cookies.dat", "wb") as f:
                pickle.dump(self.cookies, f)
            return True
        except Exception as e:
            LOG.error(str(e))
            return False

    def load_cookies(self):
        try:
            with open(DATA_PATH + "cookies.data", "rb") as f:
                self.cookies = pickle.load(f)
                requests.session().cookies = self.cookies
            return True
        except Exception as e:
            LOG.error(str(e))
            return False
