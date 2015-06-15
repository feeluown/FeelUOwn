# -*- coding:utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class MusicTableWidget(QTableWidget):
    """显示音乐信息的tablewidget

    """
    def __init__(self, rows=0, columns=4, parent=None):
        super().__init__(rows, columns, parent)
        self.set_prop()

    def set_prop(self):
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setHorizontalHeaderLabels([u'歌曲名',
                                        u'歌手',
                                        u'专辑名',
                                        u'时长'])
        self.setShowGrid(False)     # item 之间的 border
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self.setWindowFlags(Qt.FramelessWindowHint)

        self.setAlternatingRowColors(True)

    def focusOutEvent(self, event):
        self.close()

    def add_item_from_model(self, music_model):
        artist_name = ''
        music_item = QTableWidgetItem(music_model['name'])
        album_item = QTableWidgetItem(music_model['album']['name'])
        if len(music_model['artists']) > 0:
            artist_name = music_model['artists'][0]['name']
        artist_item = QTableWidgetItem(artist_name)

        duration = music_model['duration']
        m = duration / 60000
        s = (duration % 60000) / 1000
        duration = str(m) + ':' + str(s);
        duration_item = QTableWidgetItem(duration)
        
        music_item.setData(Qt.UserRole, music_model)
        row = self.rowCount()
        self.setRowCount(row + 1)
        print("row: ", row)
        self.setItem(row, 0, music_item)
        self.setItem(row, 1, artist_item)
        self.setItem(row, 2, album_item)
        self.setItem(row, 3, duration_item)

    def set_row_items(self, music_model, row):

        # to get pure dict from qvariant, so pay attension !
        # stackoverflow: how to get the original python data from qvariant
        # music = QVariant((datamodel, ))
        pass


