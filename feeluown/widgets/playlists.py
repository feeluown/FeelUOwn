import logging

from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
    QModelIndex,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
)

from .textlist import TextlistModel, TextlistView


logger = logging.getLogger(__name__)


class PlaylistsModel(TextlistModel):
    def __init__(self, parent):
        super().__init__(parent)
        self._playlists = []
        self._fav_playlists = []

    @property
    def items(self):
        return self._playlists + self._fav_playlists

    def add(self, playlist, is_fav=False):
        if is_fav:
            start = len(self._playlists) + len(self._fav_playlists)
            playlists = self._fav_playlists
        else:
            start = len(self._playlists)
            playlists = self._playlists

        if isinstance(playlist, list):
            _playlists = playlist
        else:
            _playlists = [playlist]
        end = start + len(_playlists)
        self.beginInsertRows(QModelIndex(), start, end)
        playlists.extend(_playlists)
        self.endInsertRows()

    def clear(self):
        total_length = len(self.items)
        self.beginRemoveRows(QModelIndex(), 0, total_length - 1)
        self._playlists = []
        self._fav_playlists = []
        self.endRemoveRows()

    def flags(self, index):
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.row() < len(self._playlists):
            flags |= Qt.ItemIsDropEnabled
        return flags

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        playlist = self.items[row]
        if role == Qt.DisplayRole:
            if row < len(self._playlists):
                flag = '♬ '
            else:
                flag = '★ '
            return flag + playlist.name
        return super().data(index, role)


class PlaylistsView(TextlistView):
    """歌单列表视图

    该视图会显示所有的元素，理论上不会有滚动条，也不接受滚动事件
    """
    show_playlist = pyqtSignal([object])

    def __init__(self, parent):
        super().__init__(parent)

        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        playlist = index.data(role=Qt.UserRole)
        self.show_playlist.emit(playlist)

    def dropEvent(self, e):
        mimedata = e.mimeData()
        song = mimedata.model
        index = self.indexAt(e.pos())
        playlist = index.data(Qt.UserRole)
        self._results[index.row] = (index, None)
        self.viewport().update()
        is_success = playlist.add(song.identifier)
        self._results[index.row] = (index, is_success)
        self.viewport().update()
        self._result_timer.start(2000)
        e.accept()

    def dragMoveEvent(self, e):
        mimedata = e.mimeData()
        song = mimedata.model
        index = self.indexAt(e.pos())
        playlist = index.data(Qt.UserRole)
        if song.source == playlist.source:
            e.accept()
            return
        e.ignore()

    def dragEnterEvent(self, e):
        mimedata = e.mimeData()
        if mimedata.hasFormat('fuo-model/x-song'):
            e.accept()
            return
        e.ignore()
