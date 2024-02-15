from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFontMetrics, QPalette, QColor, QPainter
from PyQt5.QtWidgets import QHBoxLayout, QStackedLayout, QWidget

from feeluown.gui.components.player_playlist import PlayerPlaylistView
from feeluown.gui.helpers import (
    fetch_cover_wrapper, palette_set_bg_color, random_solarized_color
)
from feeluown.gui.widgets import MVButton
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
        self.run_refresh_task()

    def showEvent(self, e):
        super().showEvent(e)
        if self._need_refresh:
            self.run_refresh_task()

    def run_refresh_task(self):
        self._app.task_mgr.run_afn_preemptive(self.refresh)
        self._need_refresh = False


class MVWrapper(QWidget):

    def __init__(self, parent):
        super().__init__(parent=parent)

        palette = self.palette()
        color = QColor('black')
        color.setAlpha(150)
        palette_set_bg_color(palette, color)
        palette.setColor(QPalette.Text, QColor('white'))
        palette.setColor(QPalette.Foreground, QColor('white'))
        palette.setColor(QPalette.ButtonText, QColor('white'))
        self.setPalette(palette)

        self._layout = QHBoxLayout(self)
        self.mv_btn = MVButton(length=20, parent=self)
        self.mv_btn.setToolTip('播放歌曲 MV')

        self.mv_btn.setPalette(palette)
        self._layout.addWidget(self.mv_btn)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setFixedSize(40, 25)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.palette().color(QPalette.Window))
        painter.drawRoundedRect(self.rect(), 3, 3)


class NowplayingArtwork(QWidget):

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)

        self._app = app
        self._inner = CoverLabelV2(app, self)
        self._mv_wrapper = MVWrapper(parent=self)
        self.mv_btn = self._mv_wrapper.mv_btn

        self._app.player.metadata_changed.connect(
            self.on_metadata_changed, aioqueue=True
        )
        self._app.playlist.song_mv_changed.connect(
            self.on_current_song_mv_changed, aioqueue=True
        )

        self._stacked_layout = QStackedLayout(self)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self._stacked_layout.addWidget(self._inner)
        self.layout().setAlignment(self._inner, Qt.AlignVCenter)

        self._mv_wrapper.raise_()

    def set_body(self, widget=None):
        if widget is None:
            widget = self._inner
        if widget == self._inner:
            self._stacked_layout.setCurrentWidget(self._inner)
            self._mv_wrapper.raise_()
        else:
            self._stacked_layout.addWidget(widget)
            self._stacked_layout.setCurrentWidget(widget)
            self._stacked_layout.setAlignment(widget, Qt.AlignVCenter)
            self._mv_wrapper.hide()

    def on_current_song_mv_changed(self, _, mv):
        if mv is not None:
            self._mv_wrapper.show()
        else:
            self._mv_wrapper.hide()

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

    def resizeEvent(self, a0) -> None:
        super().resizeEvent(a0)
        self._mv_wrapper.move(
            self.width() - self._mv_wrapper.width() - 10,
            self.height() - self._mv_wrapper.height() - 10
        )


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

        self._alignment = Qt.AlignCenter
        self._highlight_font_size = 25
        self._item_spacing = 20

        palette = self.palette()
        palette.setColor(QPalette.Highlight, Qt.transparent)
        palette.setColor(QPalette.HighlightedText, random_solarized_color())
        self.setPalette(palette)

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
        super().__init__(
            parent=parent,
            no_scroll_v=False,
            delegate_options={'quoted_bg_color_role': QPalette.Base}
        )

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
                hover_color_role=QPalette.Base,
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
            hover_color_role=QPalette.Base,
        )
        self.setItemDelegate(delegate)
