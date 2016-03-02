# -*- coding:utf8 -*-

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView,\
    QLabel, QTableWidgetItem, QWidget, QHBoxLayout, QPushButton

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

    def get_model(self, row):
        item = self.item(row, self._data_column_id)
        data = item.data(Qt.UserRole)
        return data

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
        if self.is_item_already_in(music_model['id']) is not False:
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
        btn.setObjectName('remove_music')
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
            self.add_item_from_model(track)

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
    signal_play_mv = pyqtSignal([int])
    signal_search_album = pyqtSignal([int])
    signal_search_artist = pyqtSignal([int])

    # 引入 tracks_type 这样一个变量，判断需要对歌曲添加哪些操作
    tracks_types = ['playlist_m', 'playlist_o', 'artist', 'album',
                    'brief', 'other']

    def __init__(self, rows=0, columns=6, parent=None):
        super().__init__(rows, columns, parent)

        self.setHorizontalHeaderLabels([u'',
                                        u'歌曲名',
                                        u'歌手',
                                        u'专辑',
                                        u'时长',
                                        u'移除'])

        self.setColumnWidth(0, 28)
        self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 200)
        self.setColumnWidth(5, 30)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        self.setObjectName('tracks_table_widget')

        self._data_column_id = 1
        self._tracks_type = 0
        self.songs = []

        self._bind_signal()

    def _bind_signal(self):
        self.cellClicked.connect(self.on_cell_clicked)

    def add_item_from_model(self, music_model, tracks_type):
        artist_name = ''
        music_item = QTableWidgetItem(music_model['name'])
        album_item = QTableWidgetItem(music_model['album']['name'])
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
        self.setItem(row, 3, album_item)
        self.setItem(row, 4, duration_item)

        if self._tracks_type is not 4:
            self.setColumnHidden(0, False)
            if MusicModel.mv_available(music_model):
                mv_label = QLabel('MV')
                mv_label.setObjectName('tracks_table_mv_btn')
                self.setCellWidget(row, 0, mv_label)
        else:
            self.setColumnHidden(0, True)

        if tracks_type is 0:
            btn = QLabel('✗')
            btn.setObjectName('tracks_table_remove_btn')
            self.setCellWidget(row, 5, btn)

        self.setRowHeight(row, 35)
        row_mid = dict()
        row_mid['mid'] = music_model['id']
        row_mid['row'] = row

        return True

    def set_songs(self, tracks, tracks_type):
        self.songs = tracks
        self.setRowCount(0)
        self.change_tracks_type(tracks_type)
        for track in tracks:
            self.add_item_from_model(track, tracks_type)

    def is_songs_brief(self):
        if self._tracks_type is 4:
            return True
        return False

    def change_tracks_type(self, tracks_type):
        self._tracks_type = tracks_type
        self._tracks_type_changed()

    def _tracks_type_changed(self):
        if self._tracks_type is not 0:
            self.setColumnHidden(5, True)
        else:
            self.setColumnHidden(5, False)

    @pyqtSlot(int, int)
    def on_cell_clicked(self, row, column):
        if column == 0:     # mv
            model = self.get_model(row)
            if MusicModel.mv_available(model):
                self.signal_play_mv.emit(model['mvid'])
        elif column == 2:   # artist
            model = self.get_model(row)
            self.signal_search_artist.emit(model['artists'][0]['id'])
        elif column == 3:    # album
            model = self.get_model(row)
            self.signal_search_album.emit(model['album']['id'])
        elif column == 4:   # remove song
            pass


class TracksTableOptionsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QHBoxLayout(self)
        self.play_all_btn = QPushButton('►')

        self.play_all_btn.setObjectName('tracks_play_all_btn')
        self.play_all_btn.setToolTip('Play All')

        self.layout.addSpacing(20)
        self.layout.addWidget(self.play_all_btn)
        self.layout.addStretch(1)

        self.setFixedHeight(40)

        self._set_layout_props()

    def _set_layout_props(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
