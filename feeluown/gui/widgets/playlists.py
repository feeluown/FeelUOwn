import logging

from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
    QModelIndex,
)
from PyQt5.QtWidgets import (
    QAbstractItemView, QMenu
)

from feeluown.library import SupportsPlaylistAddSong
from feeluown.utils.aio import run_afn, run_fn
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

    def remove(self, playlist):
        for i, playlist_ in enumerate(self._playlists):
            if playlist_ == playlist:
                self.beginRemoveRows(QModelIndex(), i, i+1)
                self._playlists.remove(playlist)
                self.endRemoveRows()
                break

        for i, playlist_ in enumerate(self._fav_playlists):
            if playlist_ == playlist:
                start = i+len(self._playlists)
                end = start + 1
                self.beginRemoveRows(QModelIndex(), start, end)
                self._fav_playlists.remove(playlist)
                self.endRemoveRows()
                break

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

    .. versiondeprecated:: 3.9
    """
    show_playlist = pyqtSignal([object])
    remove_playlist = pyqtSignal([object])

    def __init__(self, parent):
        super().__init__(parent)

        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        playlist = index.data(role=Qt.UserRole)
        self.show_playlist.emit(playlist)

    def contextMenuEvent(self, event):
        indexes = self.selectionModel().selectedIndexes()
        if len(indexes) != 1:
            return

        playlist = self.model().data(indexes[0], Qt.UserRole)
        menu = QMenu()
        action = menu.addAction('删除此歌单')
        action.triggered.connect(lambda: self.remove_playlist.emit(playlist))
        menu.exec(event.globalPos())

    def dropEvent(self, e):
        mimedata = e.mimeData()
        song = mimedata.model
        index = self.indexAt(e.pos())
        playlist = index.data(Qt.UserRole)
        self._results[index.row] = (index, None)
        self.viewport().update()

        async def do():
            is_success = False
            app = self.parent().parent()._app   # type: ignore[attr-defined]
            try:
                provider = app.library.get(playlist.source)
                if isinstance(provider, SupportsPlaylistAddSong):
                    is_success = await run_fn(provider.playlist_add_song, playlist, song)
            except:  # noqa, to avoid crash.
                logger.exception('add song to playlist failed')
                is_success = False
            app.show_msg(f"添加歌曲 {song} 到播放列表 {'成功' if is_success is True else '失败'}")
            self._results[index.row] = (index, is_success)
            self.viewport().update()
            self._result_timer.start(2000)

        run_afn(do)
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
