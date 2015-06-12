# -*- coding:utf8 -*-

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from base.common import singleton


@singleton
class NetworkManger(QNetworkAccessManager):
    def __init__(self, parent=None):
        super().__init__(parent)