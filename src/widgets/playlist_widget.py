# -*- coding=utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class PlaylistWidget(QListWidget):
    """显示音乐信息的tablewidget

    """
    def __init__(self, parent=None):
        super().__init__(parent)