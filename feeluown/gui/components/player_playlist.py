from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt, QModelIndex, QItemSelectionModel
from PyQt5.QtWidgets import QMenu, QAbstractItemView

from feeluown.utils.aio import run_fn, run_afn
from feeluown.library import (
    BriefSongModel, SupportsCurrentUserDislikeAddSong, SupportsCurrentUser,
)
from feeluown.player import PlaylistMode
from feeluown.gui.components import SongMenuInitializer
from feeluown.gui.helpers import fetch_cover_wrapper
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListView,
    SongMiniCardListModel,
)
from feeluown.utils.reader import create_reader


if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


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

    def __init__(self, app: 'GuiApp', *args, **kwargs):
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
        indexes = self.selectedIndexes()
        if not indexes:
            return

        songs = [index.data(Qt.UserRole)[0] for index in indexes]
        menu = QMenu()
        if self._app.playlist.mode is PlaylistMode.fm:
            btn_text = '不想听'
        else:
            btn_text = '从播放队列中移除'
        action = menu.addAction(btn_text)
        action.triggered.connect(lambda: self._remove_songs(songs))

        # Just hide the action instead of making it disabled when conditions are not met.
        # Because this function is not supported by most providers,
        # and (I think) most users do not use it frequently.
        if len(songs) == 1:
            song = songs[0]
            provider = self._app.library.get(song.source)
            if (
                isinstance(provider, SupportsCurrentUserDislikeAddSong)
                and isinstance(provider, SupportsCurrentUser)
                and provider.has_current_user()
            ):
                action_dislike = menu.addAction('加入资源提供方的黑名单')
                action_dislike.triggered.connect(
                    lambda: run_afn(self._dislike_and_remove_songs, songs))

        if len(songs) == 1:
            menu.addSeparator()
            SongMenuInitializer(self._app, songs[0]).apply(menu)
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

    async def _dislike_and_remove_songs(self, songs):
        song: BriefSongModel = songs[0]
        provider = self._app.library.get(song.source)
        assert isinstance(provider, SupportsCurrentUserDislikeAddSong)
        self._app.show_msg('正在加入黑名单，请稍等...', timeout=3000)
        ok = await run_fn(provider.current_user_dislike_add_song, song)
        if ok:
            self._app.show_msg('已加入黑名单')
        else:
            self._app.show_msg('加入黑名单失败', timeout=3000)
        self._remove_songs(songs)

    def _remove_songs(self, songs):
        for song in songs:
            playlist_songs = self._app.playlist.list()
            if (
                self._app.playlist.mode is PlaylistMode.fm
                # playlist_songs should not be empty, just for robustness
                and playlist_songs
                and song == self._app.playlist.current_song
                and playlist_songs[-1] == song
            ):
                self._app.show_msg("FM 模式下，如果当前歌曲是最后一首歌，则无法移除，请稍后再尝试移除", timeout=3000)
                self._app.playlist.next()
            else:
                self._app.playlist.remove(song)
