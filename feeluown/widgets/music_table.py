# -*- coding:utf8 -*-

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView,\
    QLabel, QTableWidgetItem

from feeluown.models import MusicModel


class BaseMusicTable(QTableWidget):
    '''music table widget

    items must set data whose type is MusicModel
    for example:
        >>> item.setData(Qt.UserRole, music_model)
        >>> self.setItem(item)
    '''
    signal_play_music = pyqtSignal([int], name='play_music')

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self._alignment = Qt.AlignLeft | Qt.AlignVCenter
        self.horizontalHeader().setDefaultAlignment(self._alignment)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.cellDoubleClicked.connect(self.on_cell_double_clicked)
        self.setShowGrid(False)     # item 之间的 border
        self.setMouseTracking(True)
        self.verticalHeader().hide()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAlternatingRowColors(True)

        self._data_column_id = 1

    def focus_cell_by_mid(self, mid):
        row = self.find_row_by_mid(mid)
        self.setCurrentCell(row, self._data_column_id)
        self.setCurrentItem(self.item(row, self._data_column_id))
        self.scrollToItem(self.item(row, self._data_column_id))

    def find_row_by_mid(self, mid):
        row = False
        total = self.rowCount()
        i = 0
        while i < total:
            item = self.item(i, self._data_column_id)
            data = item.data(Qt.UserRole)
            tmp_mid = data['id']
            if tmp_mid == mid:
                row = i
                break
            i += 1
        return row

    def find_mid_by_row(self, row):
        item = self.item(row, self._data_column_id)
        data = item.data(Qt.UserRole)
        mid = data['mid']
        return mid

    def is_item_already_in(self, mid):
        row = self.find_row_by_mid(mid)
        if row is not None:
            return row
        return False

    @pyqtSlot(int, int)
    def on_cell_double_clicked(self, row, column):
        item = self.item(row, self._data_column_id)
        music_model = item.data(Qt.UserRole)
        self.signal_play_music.emit(music_model['id'])


class CurrentMusicTable(BaseMusicTable):
    signal_remove_music_from_list = pyqtSignal([int],
                                               name='remove_music_from_list')

    def __init__(self, rows=0, columns=4, parent=None):
        super().__init__(rows, columns, parent)

        self.__set_prop()
        self.__init_signal_binding()
        self._data_column_id = 0

        self.resize(500, 200)

    def __set_objects_name(self):
        pass

    def __init_signal_binding(self):
        self.cellClicked.connect(self.on_remove_music_btn_clicked)

    def __set_prop(self):
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.setHorizontalHeaderLabels([u'歌曲名',
                                        u'歌手',
                                        u'时长',
                                        u'移除'])
        self.setShowGrid(False)     # item 之间的 border
        self.setMouseTracking(True)
        self.verticalHeader().hide()
        self.setFocusPolicy(Qt.StrongFocus)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

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
        btn.setText('✖')
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
            self.add_item_from_modegg(track)

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


class TracksTableWidget(BaseMusicTable):
    def __init__(self, rows=0, columns=5, parent=None):
        super().__init__(rows, columns, parent)

        self.setHorizontalHeaderLabels([u'',
                                        u'歌曲名',
                                        u'歌手',
                                        u'时长',
                                        u'移除'])

        self.setColumnWidth(0, 25)
        self.setColumnWidth(2, 200)
        self.setColumnWidth(4, 30)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        self.setObjectName('tracks_table_widget')

        self._data_column_id = 1

    def add_item_from_model(self, music_model):
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

        self.setItem(row, 1, music_item)
        self.setItem(row, 2, artist_item)
        self.setItem(row, 3, duration_item)

        music_item.setTextAlignment(self._alignment)
        artist_item.setTextAlignment(self._alignment)
        duration_item.setTextAlignment(self._alignment)

        if MusicModel.mv_available(music_model):
            mv_label = QLabel('MV')
        else:
            mv_label = QLabel('')
        mv_label.setObjectName('tracks_table_mv_btn')
        self.setCellWidget(row, 0, mv_label)

        btn = QLabel('✖')
        btn.setObjectName('tracks_table_remove_btn')
        self.setCellWidget(row, 4, btn)
        self.setRowHeight(row, 35)

        row_mid = dict()
        row_mid['mid'] = music_model['id']
        row_mid['row'] = row

        return True

    def set_songs(self, tracks):
        self.setRowCount(0)
        for track in tracks:
            self.add_item_from_model(track)
