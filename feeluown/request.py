import requests

from PyQt5.QtCore import QObject, pyqtSignal
from requests.exceptions import ConnectionError, HTTPError, Timeout


class Request(QObject):
    connected_signal = pyqtSignal()
    disconnected_signal = pyqtSignal()
    slow_signal = pyqtSignal()

    def __init__(self, app):
        super().__init__(parent=app)
        self._app = app

    def get(self, *args, **kw):
        try:
            res = requests.get(*args, **kw)
            self.connected_signal.emit()
            return res
        except ConnectionError:
            self._app.message('网络连接失败', error=True)
            self.disconnected_signal.emit()
        except HTTPError:
            self._app.message('服务端出现错误', error=True)
        except Timeout:
            self._app.message('网络连接超时', error=True)
            self.slow_signal.emit()
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
