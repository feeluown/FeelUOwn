import asyncio
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont, QPalette
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from fuocore import ModelType
from feeluown.components.songs import SongsTableModel, SongsTableView


logger = logging.getLogger(__name__)


class DescriptionContainer(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._label = QLabel(self)
        self._label.setWordWrap(True)
        self._label.setTextFormat(Qt.RichText)
        self._label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setWidget(self._label)
        self.setWidgetResizable(True)

        self.setFrameShape(QFrame.NoFrame)
        self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    @property
    def html(self):
        return self._label.text()

    def set_html(self, desc):
        self._label.setText(desc)

    def keyPressEvent(self, event):
        key_code = event.key()
        if key_code == Qt.Key_Space:
            # TODO: show more, show less
            pass
        elif key_code == Qt.Key_J:
            value = self.verticalScrollBar().value()
            self.verticalScrollBar().setValue(value + 20)
        elif key_code == Qt.Key_K:
            value = self.verticalScrollBar().value()
            self.verticalScrollBar().setValue(value - 20)
        else:
            super().keyPressEvent(event)


class TableOverview(QFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.cover_label = QLabel(self)
        self._title_label = QLabel(self)
        self._desc_container = DescriptionContainer(self)

        self._title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._desc_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self._layout = QHBoxLayout(self)
        self._right_sub_layout = QVBoxLayout()
        self._right_sub_layout.addWidget(self._title_label)
        self._right_sub_layout.addStretch(0)
        self._right_sub_layout.addWidget(self._desc_container)
        self._right_sub_layout.setStretch(2, 1)
        self._layout.addWidget(self.cover_label)
        self._layout.addSpacing(10)
        self._layout.addLayout(self._right_sub_layout)
        self._layout.setStretch(1, 1)
        self.cover_label.setFixedWidth(160)
        self.setMaximumHeight(180)

    def set_cover(self, pixmap):
        self.cover_label.setPixmap(
            pixmap.scaledToWidth(self.cover_label.width(),
                                 mode=Qt.SmoothTransformation))

    def set_name(self, name):
        self._title_label.setText('<h3>{name}</h3>'.format(name=name))
        self._title_label.setTextFormat(Qt.RichText)

    def set_desc(self, desc):
        if desc:
            self._desc_container.show()
            self._desc_container.set_html(desc)
        else:
            self._desc_container.hide()


class SongsTableContainer(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.songs_table = SongsTableView(self)
        self.table_overview = TableOverview(self)

        self._layout = QVBoxLayout(self)

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.table_overview)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.songs_table)
        self._layout.addSpacing(10)

        self.songs_table.play_song_needed.connect(
            lambda song: asyncio.ensure_future(self.play_song(song)))
        self.songs_table.show_artist_needed.connect(
            lambda artist: asyncio.ensure_future(self.show_model(artist)))
        self.songs_table.show_album_needed.connect(
            lambda album: asyncio.ensure_future(self.show_model(album)))
        self.hide()

    async def play_song(self, song):
        # TODO: fetch url asynchronous
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: song.url)
        self._app.player.play_song(song)

    def play_all(self):
        songs = self.songs_table.model().songs
        self._app.player.playlist.clear()
        for song in songs:
            self._app.player.playlist.add(song)
        self._app.player.playlist.play_next()

    async def show_model(self, model):
        model_type = model.type_
        if model_type == ModelType.album:
            func = self.show_album
        elif model_type == ModelType.artist:
            func = self.show_artist
        elif model_type == ModelType.playlist:
            func = self.show_playlist
        else:
            func = lambda model: None
        self._app.histories.append(model)
        await func(model)

    async def show_playlist(self, playlist):
        self.table_overview.show()
        loop = asyncio.get_event_loop()
        songs = await loop.run_in_executor(None, lambda: playlist.songs)
        self._show_songs(songs)
        self.table_overview.set_name(playlist.name)
        self.table_overview.set_desc(playlist.desc or '')
        if playlist.cover:
            loop.create_task(self.show_cover(playlist.cover))

    async def show_artist(self, artist):
        self.table_overview.show()
        loop = asyncio.get_event_loop()
        songs = await loop.run_in_executor(None, lambda: artist.songs)
        self.table_overview.set_desc(artist.desc or '')
        self.table_overview.set_name(artist.name)
        self._show_songs(songs)
        if artist.cover:
            loop.create_task(self.show_cover(artist.cover))

    async def show_album(self, album):
        loop = asyncio.get_event_loop()
        songs = await loop.run_in_executor(None, lambda: album.songs)
        self.table_overview.set_name(album.name)
        self.table_overview.set_desc(album.desc or '')
        self._show_songs(songs)
        if album.cover:
            loop.create_task(self.show_cover(album.cover))

    async def show_cover(self, cover):
        # FIXME: cover_hash may not work properly someday
        cover_uid = cover.split('/', -1)[-1]
        content = await self._app.img_ctl.get(cover, cover_uid)
        img = QImage()
        img.loadFromData(content)
        pixmap = QPixmap(img)
        if not pixmap.isNull():
            self.table_overview.set_cover(pixmap)

    def _show_songs(self, songs):
        self.show()
        self.songs_table.setModel(SongsTableModel(songs or []))
        self.songs_table.scrollToTop()

    def show_songs(self, songs):
        self._show_songs(songs)
        self.table_overview.hide()

    def search(self, text):
        if self.isVisible() and self.songs_table is not None:
            self.songs_table.filter_row(text)
