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

        }

    def post_and_updatecookies(self, url, data):
        try:
            res = requests.post(url, data=data, headers=self.headers, cookies=self.cookies)
            self.cookies.update(res.cookies.get_dict())
            requests.session().cookies = self.cookies
            self.save_cookies()
            return res.json()
        except Exception as e:
            LOG.error(str(e))
            return {"code": 408}
