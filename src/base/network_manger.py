# -*- coding:utf8 -*-

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from base.common import singleton


@singleton
class NetworkManager(QNetworkAccessManager):
    """
    One QNetworkAccessManager should be enough for the whole Qt application
    """
    def __init__(self, parent=None):
        super().__init__(parent)