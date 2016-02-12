# -*- coding:utf8 -*-

from queue import Queue
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply

from feeluown.controller_api import ControllerApi
from .utils import singleton
from .logger import LOG


@singleton
class NetworkManager(QNetworkAccessManager):
    """
    One QNetworkAccessManager should be enough for the whole Qt application
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.network_queue = Queue()

    @pyqtSlot(QNetworkReply)
    def access_network_queue(self, res):
        if ControllerApi.network_manager.network_queue.empty():
            LOG.info('Nothing in network queue')
            return
        item = ControllerApi.network_manager.network_queue.get_nowait()
        item(res)
