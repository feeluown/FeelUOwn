from PyQt5.QtCore import Qt, QModelIndex, QItemSelectionModel
from PyQt5.QtWidgets import QMenu, QAbstractItemView

from feeluown.gui.components import SongMenuInitializer
from feeluown.gui.helpers import fetch_cover_wrapper
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListView,
    SongMiniCardListModel,
)
from feeluown.utils.reader import create_reader


class PlayerPlaylistModel(SongMiniCardListModel):
    """
    this is a singleton class (ensured by PlayerPlaylistView)
    """

    def __init__(self, playlist, *args, **kwargs):
        reader = create_reader(playlist.list())
        super().__init__(reader, *args, **kwargs)

        self._playlist = playlist
        self._playlist.songs_added.connect(self.on_songs_added)
        self._playlist.songs_removed.connect(self.on_songs_removed)

    def flags(self, index):
        flags = super().flags(index)
        song = index.data(Qt.UserRole)[0]
        if self._playlist.is_bad(song):
            # Disable bad song.
            flags &= ~Qt.ItemIsEnabled
        return flags

    def on_songs_added(self, index, count):
        self.beginInsertRows(QModelIndex(), index, index + count - 1)
        # Insert from tail to front.
        while count > 0:
            self._items.insert(index, self._playlist[index + count - 1])
            count -= 1
        self.endInsertRows()

    def on_songs_removed(self, index, count):
        self.beginRemoveRows(QModelIndex(), index, index + count - 1)
        while count > 0:
            self._items.pop(index + count - 1)
            count -= 1
        self.endRemoveRows()


class PlayerPlaylistView(SongMiniCardListView):

    _model = None

    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        self.play_song_needed.connect(self._app.playlist.play_model)
        if PlayerPlaylistView._model is None:
            PlayerPlaylistView._model = PlayerPlaylistModel(
                self._app.playlist,
                fetch_cover_wrapper(self._app),
            )
        self.setModel(PlayerPlaylistView._model)

    def contextMenuEvent(self, e):
        index = self.indexAt(e.pos())
        if not index.isValid():
            return

        song = index.data(Qt.UserRole)[0]
        menu = QMenu()
        action = menu.addAction('从播放队列中移除')
        menu.addSeparator()
        SongMenuInitializer(self._app, song).apply(menu)

        action.triggered.connect(lambda: self._app.playlist.remove(song))
        menu.exec_(e.globalPos())

    def scroll_to_current_song(self):
        """Scroll to the current song, and select it to highlight it."""
        current_song = self._app.playlist.current_song
        songs = self._app.playlist.list()
        if current_song is not None:
            model = self.model()
            row = songs.index(current_song)
            index = model.index(row, 0)
            # In order to highlight the current song.
            self.selectionModel().select(index, QItemSelectionModel.SelectCurrent)
            self.scrollTo(index, QAbstractItemView.PositionAtCenter)
