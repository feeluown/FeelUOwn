# -*- coding:utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from base.logger import LOG


class MusicTableWidget(QTableWidget):
    """显示音乐信息的tablewidget

    """

    signal_play_music = pyqtSignal([int], name='play_music')
    signal_remove_music_from_list = pyqtSignal([int], name='remove_music_from_list')

    def __init__(self, rows=0, columns=4, parent=None):
        super().__init__(rows, columns, parent)

        self.__row_mid_map = []   # row 为 index, mid为值
        self.__special_focus_out = False

        self.__signal_mapper = QSignalMapper()  # 把remove_music按钮和mid关联起来
        self._alignment = Qt.AlignLeft | Qt.AlignVCenter
        
        self.__set_prop()
        self.__init_signal_binding()

    def __set_objects_name(self):
        pass

    def __init_signal_binding(self):
        self.cellDoubleClicked.connect(self.on_cell_double_clicked)
        self.cellClicked.connect(self.on_remove_music_btn_clicked)

    def __set_prop(self):
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setDefaultAlignment(self._alignment)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setHorizontalHeaderLabels([u'歌曲名',
                                        u'歌手',
                                        u'时长',
                                        u'移除'])
        self.setShowGrid(False)     # item 之间的 border
        self.setMouseTracking(True)
        self.verticalHeader().hide()
        self.setFocusPolicy(Qt.StrongFocus)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)

        self.setAlternatingRowColors(True)

    def focusOutEvent(self, event):
        self.close()

    def add_item_from_model(self, music_model):
        if self.is_item_already_in(music_model['id']) is not False:     # is
            return False

        artist_name = ''
        music_item = QTableWidgetItem(music_model['name'])
        if len(music_model['artists']) > 0:
            artist_name = music_model['artists'][0]['name']
        artist_item = QTableWidgetItem(artist_name)

        duration = music_model['duration']
        m = int(duration / 60000)
        s = int((duration % 60000) / 1000)
        duration = str(m) + ':' + str(s)
        duration_item = QTableWidgetItem(duration)

        music_item.setData(Qt.UserRole, music_model)
        row = self.rowCount()
        self.setRowCount(row + 1)

        self.setItem(row, 0, music_item)
        self.setItem(row, 1, artist_item)
        self.setItem(row, 2, duration_item)

        music_item.setTextAlignment(self._alignment)
        artist_item.setTextAlignment(self._alignment)
        duration_item.setTextAlignment(self._alignment)

        btn = QLabel()
        btn.setToolTip(u'从当前播放列表中移除')
        btn.setObjectName('remove_music')   # 为了应用QSS，不知道这种实现好不好
        self.setCellWidget(row, 3, btn)
        self.setRowHeight(row, 30)
        self.setColumnWidth(3, 30)

        row_mid = dict()
        row_mid['mid'] = music_model['id']
        row_mid['row'] = row

        return True

    def set_songs(self, tracks):
        self.setRowCount(0)
        for track in tracks:
            self.add_item_from_model(track)

    def is_item_already_in(self, mid):
        row = self.find_row_by_mid(mid)
        if row is not None:
            return row
        return False

    def focus_cell_by_mid(self, mid):
        row = self.find_row_by_mid(mid)
        self.setCurrentCell(row, 0)
        self.setCurrentItem(self.item(row, 0))
        self.scrollToItem(self.item(row, 0))

    def find_row_by_mid(self, mid):
        row = False
        total = self.rowCount()
        i = 0
        while i < total:
            item = self.item(i, 0)
            data = item.data(Qt.UserRole)
            tmp_mid = data['id']
            if tmp_mid == mid:
                row = i
                break
            i += 1
        return row

    def find_mid_by_row(self, row):
        item = self.item(row, 0)
        data = item.data(Qt.UserRole)
        mid = data['mid']
        return mid


    @pyqtSlot(int, int)
    def on_cell_double_clicked(self, row, column):
        item = self.item(row, 0)
        music_model = item.data(Qt.UserRole)
        self.signal_play_music.emit(music_model['id'])

    @pyqtSlot(int, int)
    def on_remove_music_btn_clicked(self, row, column):
        if column != 3:
            return

        item = self.item(row, 0)
        data = item.data(Qt.UserRole)
        mid = data['id']
        row = self.find_row_by_mid(mid)
        self.removeRow(row)
        self.signal_remove_music_from_list.emit(mid)