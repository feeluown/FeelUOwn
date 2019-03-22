import asyncio
import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from fuocore import ModelType
from feeluown.helpers import use_mac_theme, async_run
from feeluown.widgets.songs_table import SongsTableModel, SongsTableView


logger = logging.getLogger(__name__)


class DescriptionContainer(QScrollArea):

    space_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._label = QLabel(self)
        self._label.setWordWrap(True)
        self._label.setTextFormat(Qt.RichText)
        self._label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setWidget(self._label)

        self._setup_ui()

    def _setup_ui(self):
        self._label.setAlignment(Qt.AlignTop)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
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
        if key_code == Qt.Key_J:
            value = self.verticalScrollBar().value()
            self.verticalScrollBar().setValue(value + 20)
        elif key_code == Qt.Key_K:
            value = self.verticalScrollBar().value()
            self.verticalScrollBar().setValue(value - 20)
        elif key_code == Qt.Key_Space:
            self.space_pressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class TableToolbar(QWidget):
    _desc_btn_checked_text = '折叠'
    _desc_btn_unchecked_text = '展开描述'

    play_all_needed = pyqtSignal()
    toggle_desc_needed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.play_all_btn = QPushButton('播放全部', self)
        self.desc_btn = QPushButton(self._desc_btn_unchecked_text, self)
        self.play_all_btn.clicked.connect(self.play_all_needed.emit)
        self.desc_btn.clicked.connect(self.on_desc_btn_toggled)
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.play_all_btn)
        self._layout.addStretch(1)
        self._layout.addWidget(self.desc_btn)
        self._layout.addStretch(0)

    def on_desc_btn_toggled(self, checked):
        if checked:
            self.play_all_btn.hide()
            self.desc_btn.setText(self._desc_btn_checked_text)
        else:
            self.play_all_btn.show()
            self.desc_btn.setText(self._desc_btn_unchecked_text)
        self.toggle_desc_needed.emit()


class SongsTableContainer(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.songs_table = SongsTableView(self)
        self._toolbar = TableToolbar(self)
        self._cover_label = QLabel(self)
        self._desc_container_folded = True
        self._desc_container = DescriptionContainer(self)
        self._top_container = QWidget(self)
        self._cover_container = QWidget(self._top_container)

        self.songs_table.play_song_needed.connect(
            lambda song: asyncio.ensure_future(self.play_song(song)))
        self.songs_table.show_artist_needed.connect(
            lambda artist: self._app.browser.goto(model=artist))
        self.songs_table.show_album_needed.connect(
            lambda album: self._app.browser.goto(model=album))

        self._desc_container.space_pressed.connect(self.toggle_desc_container_fold)
        self._toolbar.toggle_desc_needed.connect(self.toggle_desc_container_fold)
        self._toolbar.play_all_needed.connect(self.play_all)

        self.hide()
        self._setup_ui()

    def _setup_ui(self):
        self._left_sub_layout = QVBoxLayout(self._cover_container)
        self._top_layout = QHBoxLayout(self._top_container)
        self._layout = QVBoxLayout(self)

        self._cover_label.setMinimumWidth(200)
        self._right_sub_layout = QVBoxLayout()
        self._right_sub_layout.addWidget(self._desc_container)
        self._right_sub_layout.addWidget(self._toolbar)
        self._left_sub_layout.addWidget(self._cover_label)
        self._left_sub_layout.addStretch(0)
        # 根据 Qt 文档中所说，在大部分平台中，ContentMargin 为 11
        self._left_sub_layout.setContentsMargins(0, 0, 11, 0)
        self._left_sub_layout.setSpacing(0)

        self._top_layout.addWidget(self._cover_container)
        self._top_layout.addLayout(self._right_sub_layout)
        self._top_layout.setStretch(1, 1)

        self.setAutoFillBackground(False)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self._top_container)
        self._layout.addWidget(self.songs_table)

        self._top_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        # FIXME: 更好的计算宽度和高度
        # 目前是假设知道自己初始化高度大约是 530px
        # 之后可以考虑按比例来计算
        self.overview_height = 180
        self._top_container.setMaximumHeight(self.overview_height)
        self._songs_table_height = 530 - self.overview_height
        self.songs_table.setMinimumHeight(self._songs_table_height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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

    def set_desc(self, desc):
        self._desc_container.show()
        self._desc_container.set_html(desc)

    async def show_playlist(self, playlist):
        self._top_container.show()
        loop = asyncio.get_event_loop()
        if playlist.meta.allow_create_songs_g:
            songs_g = playlist.create_songs_g()
            self._show_songs(songs_g=songs_g)
        else:
            songs = await async_run(lambda: playlist.songs, loop=loop)
            self._show_songs(songs)
        desc = '<h2>{}</h2>\n{}'.format(playlist.name, playlist.desc or '')
        self.set_desc(desc)
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
        self._top_container.show()
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
        self.set_desc(desc or '<h2>{}</h2>'.format(artist.name))
        if artist.cover:
            loop.create_task(self.show_cover(artist.cover))

    async def show_album(self, album):
        self._top_container.show()
        loop = asyncio.get_event_loop()
        songs = await async_run(lambda: album.songs)
        self._show_songs(songs)
        desc = await async_run(lambda: album.desc)
        self.set_desc(desc or '<h2>{}</h2>'.format(album.name))
        if album.cover:
            loop.create_task(self.show_cover(album.cover))

    def show_collection(self, collection):
        self._top_container.hide()
        self.show_songs(collection.models)
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
        self._show_songs(songs)
        self._top_container.show()
        self.hide_desc()
        self.hide_cover()

    def set_cover(self, pixmap):
        self._cover_container.show()
        self._cover_label.setPixmap(
            pixmap.scaledToWidth(self._cover_label.width(),
                                 mode=Qt.SmoothTransformation))

    def toggle_desc_container_fold(self):
        # TODO: add toggle animation?
        if self._desc_container_folded:
            self._top_container.setMaximumHeight(4000)
            self.songs_table.hide()
            self._desc_container_folded = False
        else:
            self._top_container.setMaximumHeight(self.overview_height)
            self.songs_table.show()
            self._desc_container_folded = True

    def search(self, text):
        if self.isVisible() and self.songs_table is not None:
            self.songs_table.filter_row(text)

    def hide_cover(self):
        self._cover_container.hide()

    def hide_desc(self):
        self._desc_container.hide()
