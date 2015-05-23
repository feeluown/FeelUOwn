# -*- coding:utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class MusicTableWidget(QTableWidget):
    """显示音乐信息的tablewidget

    """
    def __init__(self, rows=0, columns=3, parent=None):
        super(MusicTableWidget, self).__init__(rows, columns, parent)
        self.set_prop()

    def set_prop(self):
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setHorizontalHeaderLabels([u'歌曲名',
                                        u'歌手',
                                        u'专辑名'])
        self.setShowGrid(False)     # item 之间的 border
        self.setMouseTracking(True)

        self.setFocusPolicy(Qt.NoFocus)

        self.setAlternatingRowColors(True)

    def setRowItems(self, datamodel, row):
        musicItem = QTableWidgetItem(datamodel['name'])
        albumItem = QTableWidgetItem(datamodel['album']['name'])
        if len(datamodel['artists']) > 0:
            artistName = datamodel['artists'][0]['name']
        artistItem = QTableWidgetItem(artistName)
        # to get pure dict from qvariant, so pay attension !
        # stackoverflow: how to get the original python data from qvariant
        # music = QVariant((datamodel, ))
        music = datamodel
        musicItem.setData(Qt.UserRole, music)

        self.setItem(row, 0, musicItem)
        self.setItem(row, 1, artistItem)
        self.setItem(row, 2, albumItem)
