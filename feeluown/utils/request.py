import logging
import requests

from feeluown.utils.dispatch import Signal
from requests.exceptions import ConnectionError, HTTPError, Timeout


logger = logging.getLogger(__name__)


class Request:
    def __init__(self):
        self.connected_signal = Signal()
        self.disconnected_signal = Signal()
        self.slow_signal = Signal()
        self.server_error_signal = Signal()

    def get(self, *args, **kw):
        logger.info('request.get %s %s' % (args, kw))
        if kw.get('timeout') is None:
            kw['timeout'] = 1
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
        logger.info('request.post %s %s' % (args, kw))
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
