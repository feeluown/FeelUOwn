import requests

from PyQt5.QtCore import QObject, pyqtSignal
from requests.exceptions import ConnectionError, HTTPError, Timeout


class Request(QObject):
    connected_signal = pyqtSignal()
    disconnected_signal = pyqtSignal()
    slow_signal = pyqtSignal()
    server_error_signal = pyqtSignal()

    def __init__(self, app):
        super().__init__(parent=app)
        self._app = app

    def get(self, *args, **kw):
        if kw.get('timeout') is None:
            kw['timeout'] = 3
        try:
            res = requests.get(*args, **kw)
            self.connected_signal.emit()
            return res
        except ConnectionError:
            self.disconnected_signal.emit()
        except HTTPError:
            self.server_error_signal.emit()
        except Timeout:
            self.slow_signal.emit()
        return None

    def post(self, *args, **kw):
        try:
            res = requests.post(*args, **kw)
            return res
        except ConnectionError:
            self.disconnected_signal.emit()
        except HTTPError:
            self.server_error_signal.emit()
        except Timeout:
            self.slow_signal.emit()
        return None
