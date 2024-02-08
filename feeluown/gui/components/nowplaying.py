from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from feeluown.gui.components.player_playlist import PlayerPlaylistView
from feeluown.gui.helpers import fetch_cover_wrapper
from feeluown.gui.widgets.comment_list import CommentListView, CommentListModel
from feeluown.gui.widgets.cover_label import CoverLabelV2
from feeluown.gui.widgets.lyric import LyricView
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListDelegate, SongMiniCardListView, SongMiniCardListModel
)
from feeluown.library import SupportsSongHotComments, SupportsSongSimilar
from feeluown.utils.aio import run_fn, run_afn
from feeluown.utils.reader import create_reader

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class RefreshOnSongChangedMixin:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._need_refresh = True
        self._app.playlist.song_changed.connect(
            lambda song: run_afn(self.on_song_changed, song), aioqueue=True, weak=False
        )

    async def on_song_changed(self, _):
        if not self.isVisible():
            self._need_refresh = True
            return
        print('song changed, run refresh task')
        self.run_refresh_task()

    def showEvent(self, e):
        super().showEvent(e)
        if self._need_refresh:
            self.run_refresh_task()

    def run_refresh_task(self):
        self._app.task_mgr.run_afn_preemptive(self.refresh)
        self._need_refresh = False


class NowplayingArtwork(QWidget):

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)

        self._app = app
        self._inner = CoverLabelV2(app, self)
        self._app.player.metadata_changed.connect(
            self.on_metadata_changed, aioqueue=True
        )

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch(0)
        self._layout.addWidget(self._inner)
        self._layout.addStretch(0)

    def on_metadata_changed(self, metadata):
        metadata = metadata or {}
        released = metadata.get('released', '')
        if released:
            self.setToolTip(f'专辑发行日期：{released}')
        else:
            self.setToolTip('')
        # Set song artwork.
        artwork = metadata.get('artwork', '')
        artwork_uid = metadata.get('uri', artwork)
        if artwork:
            run_afn(self._inner.show_cover, artwork, artwork_uid)
        else:
            self._inner.show_img(None)


class NowplayingLyricView(LyricView):
    """
    Let user zoom in/out.
    """

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._app.live_lyric.lyrics_changed.connect(self.on_lyric_changed, aioqueue=True)
        self._app.live_lyric.line_changed.connect(self.on_line_changed, weak=True)

        font = self.font()
        font.setPixelSize(17)
        self.setFont(font)
        self.viewport().setAutoFillBackground(False)

        self._alignment = Qt.AlignCenter
        self._highlight_font_size = 25
        self._item_spacing = 20

    def _create_item(self, line):
        item = super()._create_item(line)
        rect = QFontMetrics(item.font()).boundingRect(line)
        size = QSize(rect.width(), rect.height() + self._item_spacing)
        item.setData(Qt.UserRole, (line, size))
        item.setSizeHint(size)
        return item

    def on_item_changed(self, current, previous):
        super().on_item_changed(current, previous)

        if current:
            line, size_hint = current.data(Qt.UserRole)
            rect = QFontMetrics(current.font()).boundingRect(line)
            current.setSizeHint(
                QSize(
                    size_hint.width(),
                    rect.height() + self._item_spacing,
                )
            )

    def reset_item(self, item):
        super().reset_item(item)
        if item:
            item.setSizeHint(item.data(Qt.UserRole)[1])


class NowplayingCommentListView(RefreshOnSongChangedMixin, CommentListView):

    def __init__(self, app: 'GuiApp', parent=None):
        self._app = app
        super().__init__(parent=parent, no_scroll_v=False)
        # self.viewport().setAutoFillBackground(False)

    async def refresh(self):
        song = self._app.playlist.current_song
        reader = create_reader([])
        if song is not None:
            provider = self._app.library.get(song.source)
            if isinstance(provider, SupportsSongHotComments):
                comments = await run_fn(provider.song_list_hot_comments, song)
                reader = create_reader(comments)
        self.setModel(CommentListModel(reader))  # type: ignore


class NowplayingSimilarSongsView(RefreshOnSongChangedMixin, SongMiniCardListView):

    def __init__(self, app: 'GuiApp', parent=None):
        self._app = app
        super().__init__(parent=parent, no_scroll_v=False)
        self.setItemDelegate(
            SongMiniCardListDelegate(
                self,
                card_min_width=200,
                card_height=40,
                card_padding=(5 + SongMiniCardListDelegate.img_padding, 5, 0, 5),
                card_right_spacing=10,
            )
        )

    async def refresh(self):
        song = self._app.playlist.current_song
        reader = create_reader([])
        if song is not None:
            provider = self._app.library.get(song.source)
            if isinstance(provider, SupportsSongSimilar):
                songs = await run_fn(provider.song_list_similar, song)
                reader = create_reader(songs)
        self.setModel(SongMiniCardListModel(reader, fetch_cover_wrapper(self._app)))


class NowplayingPlayerPlaylistView(PlayerPlaylistView):

    def __init__(self, app, parent=None, **kwargs):
        kwargs.setdefault('no_scroll_v', False)
        kwargs.setdefault('row_height', 60)
        super().__init__(app, parent=parent, **kwargs)

        delegate = SongMiniCardListDelegate(
            self,
            card_min_width=200,
            card_height=40,
            card_padding=(5 + SongMiniCardListDelegate.img_padding, 5, 0, 5),
            card_right_spacing=10,
        )
        self.setItemDelegate(delegate)
