# -*- coding=utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from setting import ICON_PATH


class PlaylistWidget(QListWidget):
    """显示音乐信息的tablewidget

    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_widget_prop()
        self.debug()

    def set_widget_prop(self):
        self.setWordWrap(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)

    def sizeHint(self):
        i, height = 0, 0
        while i < self.count():
            self.item(i).setSizeHint(QSize(self.item(i).sizeHint().width(), 30))
            i += 1
        height = self.sizeHintForRow(0) * self.count()
        width = self.sizeHintForColumn(0)
        return QSize(width, height)

    def set_playlist_item(self, playlist_model):
        
        pass

    def debug(self):
        icon = QIcon(ICON_PATH + 'playlist.png')
        test1 = QListWidgetItem(icon, u'我的歌曲列表')
        test2 = QListWidgetItem(icon, u'我的歌曲列表我的歌曲列表我的歌曲列表我的歌曲列表')
        test3 = QListWidgetItem(icon, u'我的歌曲列表')
        test4 = QListWidgetItem(icon, u'我的歌曲列表')
        test5 = QListWidgetItem(icon, u'我的歌曲列表')
        self.addItem(test1)
        self.addItem(test2)
        self.addItem(test3)
        self.addItem(test4)
        self.addItem(test5)
