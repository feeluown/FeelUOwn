import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout


class Request(object):
    def __init__(self, app):
        self._app = app

    def get(self, *args, **kw):
        try:
            res = requests.get(*args, **kw)
            return res
        except ConnectionError:
            self._app.message('网络连接失败', error=True)
        except HTTPError:
            self._app.message('服务端出现错误', error=True)
        except Timeout:
            self._app.message('网络连接超时', error=True)
        return None

    def post(self, *args, **kw):
        try:
            res = requests.post(*args, **kw)
            return res
        except ConnectionError:
            self._app.message('网络连接失败', error=True)
        except HTTPError:
            self._app.message('服务端出现错误', error=True)
        except Timeout:
            self._app.message('网络连接超时', error=True)
        return None
