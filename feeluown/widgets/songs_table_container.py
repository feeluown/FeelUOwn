import asyncio
import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QTabBar,
    QTabWidget,
)

from fuocore import ModelType
from feeluown.helpers import use_mac_theme, async_run
from feeluown.widgets.songs_table import SongsTableModel, SongsTableView
from feeluown.widgets.songs_table_meta import SongsTableMetaWidget

logger = logging.getLogger(__name__)


class SongsTableContainer(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.meta_widget = SongsTableMetaWidget(parent=self)
        self.songs_table = SongsTableView(parent=self)

        self.songs_table.play_song_needed.connect(
            lambda song: asyncio.ensure_future(self.play_song(song)))
        self.songs_table.show_artist_needed.connect(
            lambda artist: self._app.browser.goto(model=artist))
        self.songs_table.show_album_needed.connect(
            lambda album: self._app.browser.goto(model=album))

        self.meta_widget.toolbar.play_all_needed.connect(self.play_all)
        self.meta_widget.toggle_full_window_needed.connect(self.toggle_meta_full_window)

        self.hide()
        self._setup_ui()

    def _setup_ui(self):
        self.setAutoFillBackground(False)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.meta_widget)
        self._layout.addWidget(self.songs_table)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    async def play_song(self, song):
        await async_run(lambda: song.url)
        self._app.player.play_song(song)

    def play_all(self):
        songs = self.songs_table.model().songs
        self._app.player.playlist.clear()
        for song in songs:
            self._app.player.playlist.add(song)
        self._app.player.play_next()

    async def show_model(self, model):
        model_type = ModelType(model._meta.model_type)
        if model_type == ModelType.album:
            func = self.show_album
        elif model_type == ModelType.artist:
            func = self.show_artist
        elif model_type == ModelType.playlist:
            func = self.show_playlist
        else:
            def func(model): pass  # seems silly
        await func(model)

    def show_player_playlist(self, songs):
        self.show_songs(songs)
        self.songs_table.song_deleted.connect(
            lambda song: self._app.playlist.remove(song))

    async def show_playlist(self, playlist):
        loop = asyncio.get_event_loop()
        if playlist.meta.allow_create_songs_g:
            songs_g = playlist.create_songs_g()
            self._show_songs(songs_g=songs_g)
        else:
            songs = await async_run(lambda: playlist.songs, loop=loop)
            self._show_songs(songs)
        self.meta_widget.clear()
        self.meta_widget.title = playlist.name
        desc = await async_run(lambda: playlist.desc)
        self.meta_widget.desc = desc
        if playlist.cover:
            loop.create_task(self.show_cover(playlist.cover))

        def remove_song(song):
            model = self.songs_table.model()
            row = model.songs.index(song)
            msg = 'remove {} from {}'.format(song, playlist)
            with self._app.create_action(msg) as action:
                rv = playlist.remove(song.identifier)
                if rv:
                    model.removeRow(row)
                else:
                    action.failed()
        self.songs_table.song_deleted.connect(lambda song: remove_song(song))

    async def show_artist(self, artist):
        loop = asyncio.get_event_loop()
        songs = songs_g = None
        if artist.meta.allow_create_songs_g:
            songs_g = artist.create_songs_g()
        else:
            songs = await async_run(lambda: artist.songs)
        if songs_g is not None:
            self._show_songs(songs_g=songs_g)
        else:
            self._show_songs(songs=songs)
        desc = await async_run(lambda: artist.desc)
        self.meta_widget.clear()
        self.meta_widget.title = artist.name
        self.meta_widget.desc = desc
        if artist.cover:
            loop.create_task(self.show_cover(artist.cover))

    async def show_album(self, album):
        loop = asyncio.get_event_loop()
        songs = await async_run(lambda: album.songs)
        self.meta_widget.clear()
        self._show_songs(songs)
        desc = await async_run(lambda: album.desc)
        self.meta_widget.title = album.name
        self.meta_widget.desc = desc
        if album.cover:
            loop.create_task(self.show_cover(album.cover))

    def show_collection(self, collection):
        self.meta_widget.clear()
        self.meta_widget.title = collection.name
        self.meta_widget.updated_at = collection.updated_at
        self.meta_widget.created_at = collection.created_at
        self._show_songs(collection.models)
        self.songs_table.song_deleted.connect(collection.remove)

    async def show_url(self, url):
        model = self._app.protocol.get_model(url)
        if model.meta.model_type == ModelType.song:
            self._app.player.play_song(model)
        else:
            # TODO: add artist/album/user support
            self._app.show_msg('暂时只支持歌曲，不支持其它歌曲资源')

    async def show_cover(self, cover):
        # FIXME: cover_hash may not work properly someday
        cover_uid = cover.split('/', -1)[-1]
        content = await self._app.img_mgr.get(cover, cover_uid)
        img = QImage()
        img.loadFromData(content)
        pixmap = QPixmap(img)
        if not pixmap.isNull():
            self.set_cover(pixmap)
            self.update()

    def _show_songs(self, songs=None, songs_g=None):
        try:
            self.songs_table.song_deleted.disconnect()
        except TypeError:  # no connections at all
            pass
        self.show()
        self.songs_table.show()
        songs = songs or []
        logger.debug('Show songs in table, total: %d', len(songs))
        source_name_map = {p.identifier: p.name for p in self._app.library.list()}
        if songs_g is not None:  # 优先使用生成器
            self.songs_table.setModel(SongsTableModel(
                source_name_map=source_name_map,
                songs_g=songs_g,
                parent=self.songs_table))
        else:
            self.songs_table.setModel(SongsTableModel(
                songs=songs,
                source_name_map=source_name_map,
                parent=self.songs_table
            ))
        self.songs_table.scrollToTop()

    def show_songs(self, songs):
        self.meta_widget.clear()
        self._show_songs(songs)

    def search(self, text):
        if self.isVisible() and self.songs_table is not None:
            self.songs_table.filter_row(text)

    def set_cover(self, pixmap):
        self.meta_widget.set_cover_pixmap(pixmap)

    def toggle_meta_full_window(self, fullwindow_needed):
        if fullwindow_needed:
            self.songs_table.hide()
        else:
            self.songs_table.show()
