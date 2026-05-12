from typing import TYPE_CHECKING, Optional
import logging

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFontMetrics, QPalette, QColor, QPainter
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from feeluown.gui.components.player_playlist import PlayerPlaylistView
from feeluown.gui.helpers import (
    fetch_cover_wrapper,
    palette_set_bg_color,
    random_solarized_color,
)
from feeluown.gui.widgets import MVButton
from feeluown.gui.widgets.comment_list import CommentListView, CommentListModel
from feeluown.gui.widgets.cover_label import CoverLabelV2
from feeluown.gui.widgets.lyric import LyricView
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListDelegate,
    SongMiniCardListView,
    SongMiniCardListModel,
)
from feeluown.i18n import t
from feeluown.library import SupportsSongHotComments, SupportsSongSimilar
from feeluown.utils.aio import run_fn, run_afn
from feeluown.utils.reader import create_reader

logger = logging.getLogger(__name__)

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


class CommentSourceState:
    def __init__(self):
        self._song = None
        self._source_song_map = {}
        self._current_source_id: Optional[str] = None

    @property
    def song(self):
        return self._song

    @property
    def current_source_id(self):
        return self._current_source_id

    def reset(self, song=None):
        self._song = song
        self._source_song_map = {}
        self._current_source_id = None
        if song is not None:
            self._source_song_map[song.source] = song
            self._current_source_id = song.source

    def set_standby_map(self, standby_map):
        if self._song is None:
            return
        self._source_song_map = {self._song.source: self._song}
        self._source_song_map.update(standby_map)

    def source_ids(self):
        return self._source_song_map.keys()

    def has_standby_sources(self):
        if self._song is None:
            return False
        return len(self._source_song_map) > 1

    def get_song(self, source_id):
        return self._source_song_map.get(source_id)

    def set_current_source(self, source_id):
        self._current_source_id = source_id

    def belongs_to(self, song):
        return self._song is song


class MVWrapper(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)

        palette = self.palette()
        color = QColor("black")
        color.setAlpha(150)
        palette_set_bg_color(palette, color)
        palette.setColor(QPalette.ColorRole.Text, QColor("white"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("white"))
        self.setPalette(palette)

        self._layout = QHBoxLayout(self)
        self.mv_btn = MVButton(length=20, parent=self)
        self.mv_btn.setToolTip(t("track-movie-play-tooltip"))

        self.mv_btn.setPalette(palette)
        self._layout.addWidget(self.mv_btn)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setFixedSize(40, 25)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.palette().color(QPalette.ColorRole.Window))
        painter.drawRoundedRect(self.rect(), 3, 3)


class NowplayingArtwork(QWidget):
    def __init__(self, app: "GuiApp", parent=None):
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
        self.layout().setAlignment(self._inner, Qt.AlignmentFlag.AlignVCenter)

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
            self._stacked_layout.setAlignment(widget, Qt.AlignmentFlag.AlignVCenter)
            self._mv_wrapper.hide()

    def on_current_song_mv_changed(self, _, mv):
        if mv is not None:
            self._mv_wrapper.show()
        else:
            self._mv_wrapper.hide()

    def on_metadata_changed(self, metadata):
        metadata = metadata or {}
        released = metadata.get("released", "")
        if released:
            self.setToolTip(t("track-album-release-date", releaseDate=released))
        else:
            self.setToolTip("")
        # Set song artwork.
        artwork = metadata.get("artwork", "")
        source = metadata.get("source", "")
        artwork_uid = metadata.get("uri", artwork)
        if artwork:
            run_afn(self._inner.show_cover_with_source, artwork, source, artwork_uid)
        else:
            self._inner.show_img(None)

    def resizeEvent(self, a0) -> None:
        super().resizeEvent(a0)
        self._mv_wrapper.move(
            self.width() - self._mv_wrapper.width() - 10,
            self.height() - self._mv_wrapper.height() - 10,
        )


class NowplayingLyricView(LyricView):
    """
    Let user zoom in/out.
    """

    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._app.live_lyric.lyrics_changed.connect(
            self.on_lyric_changed, aioqueue=True
        )
        self._app.live_lyric.line_changed.connect(self.on_line_changed, weak=True)

        font = self.font()
        font.setPixelSize(17)
        self.setFont(font)

        self._alignment = Qt.AlignmentFlag.AlignCenter
        self._highlight_font_size = 25
        self._item_spacing = 20

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Highlight, Qt.GlobalColor.transparent)
        palette.setColor(QPalette.ColorRole.HighlightedText, random_solarized_color())
        self.setPalette(palette)

    def _create_item(self, line):
        item = super()._create_item(line)
        rect = QFontMetrics(item.font()).boundingRect(line)
        size = QSize(rect.width(), rect.height() + self._item_spacing)
        item.setData(Qt.ItemDataRole.UserRole, (line, size))
        item.setSizeHint(size)
        return item

    def on_item_changed(self, current, previous):
        super().on_item_changed(current, previous)

        if current:
            line, size_hint = current.data(Qt.ItemDataRole.UserRole)
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
            item.setSizeHint(item.data(Qt.ItemDataRole.UserRole)[1])


class NowplayingCommentListView(RefreshOnSongChangedMixin, QWidget):
    def __init__(self, app: "GuiApp", parent=None):
        self._app = app
        super().__init__(parent=parent)

        self._platform_selector = QComboBox(self)
        self._platform_selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self._comment_list = CommentListView(
            parent=self,
            no_scroll_v=False,
            delegate_options={"quoted_bg_color_role": QPalette.ColorRole.Base},
        )

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.addWidget(self._platform_selector)
        self._layout.addWidget(self._comment_list)

        self._platform_selector.hide()
        self._platform_selector.currentIndexChanged.connect(
            lambda idx: self._app.task_mgr.run_afn_preemptive(
                self._on_platform_changed, idx
            )
        )

        self._source_state = CommentSourceState()

    def viewport(self):
        return self._comment_list.viewport()

    def setModel(self, model):
        self._comment_list.setModel(model)

    def min_height(self):
        return self._comment_list.min_height()

    async def refresh(self):
        song = self._app.playlist.current_song
        if song is None:
            self._comment_list.setModel(CommentListModel(create_reader([])))
            self._platform_selector.hide()
            self._source_state.reset()
            return

        self._source_state.reset(song)

        # Load current platform comments.
        reader = create_reader([])
        provider = self._app.library.get(song.source)
        if isinstance(provider, SupportsSongHotComments):
            comments = await run_fn(provider.song_list_hot_comments, song)
            reader = create_reader(comments)
        self._comment_list.setModel(CommentListModel(reader))

        # Find the same song on other platforms that support hot comments.
        # Reset state and hide the selector before the async search so
        # stale entries from the previous song are not shown in the interim.
        self._platform_selector.hide()
        standby_map = await self._find_standby_songs(song)
        if self._source_state.belongs_to(song):
            self._source_state.set_standby_map(standby_map)
        self._update_platform_selector(song)

    async def _find_standby_songs(self, song):
        """Search all providers for the same song.

        Returns a dict mapping source_id -> matched BriefSongModel.
        Only includes providers that support hot comments.
        """
        # Count how many other providers support hot comments so we can
        # stop searching once every eligible provider has been matched.
        comment_providers = {
            p.identifier
            for p in self._app.library.list()
            if p.identifier != song.source
            and isinstance(p, SupportsSongHotComments)
        }
        if not comment_providers:
            return {}

        try:
            return await self._app.library.a_match_song(
                song, source_in=list(comment_providers)
            )
        except Exception:
            logger.exception("Standby song search failed")

        return {}

    def _update_platform_selector(self, song):
        self._platform_selector.blockSignals(True)
        try:
            self._platform_selector.clear()

            # First item: current platform.
            current_provider = self._app.library.get(song.source)
            current_name = current_provider.name if current_provider else song.source
            self._platform_selector.addItem(current_name, song.source)

            # Additional items: other platforms with a matched song.
            for source_id in self._source_state.source_ids():
                if source_id == song.source:
                    continue
                provider = self._app.library.get(source_id)
                name = provider.name if provider else source_id
                self._platform_selector.addItem(name, source_id)

            self._platform_selector.setVisible(
                self._source_state.has_standby_sources()
            )
            self._platform_selector.setCurrentIndex(0)
        finally:
            self._platform_selector.blockSignals(False)

    async def _on_platform_changed(self, index):
        if index < 0:
            return
        source_id = self._platform_selector.itemData(index)
        if source_id == self._source_state.current_source_id:
            return

        # Guard: if the current song has changed since this platform-switch
        # was initiated, discard the result — a subsequent refresh will
        # have reset source state and rebuilt the source-to-song map.
        song = self._source_state.get_song(source_id)
        if song is None:
            return
        provider = self._app.library.get(source_id)
        if not isinstance(provider, SupportsSongHotComments):
            return

        # Capture the song this source data belongs to.  If the song
        # changes while we're fetching comments, the last check below
        # will discard the now-stale result.
        current_song = self._source_state.song

        # Disable the selector during the fetch — keep the current comments
        # visible so there's no flicker and they're not lost on failure.
        self._platform_selector.setEnabled(False)
        try:
            comments = await run_fn(provider.song_list_hot_comments, song)
        except Exception:
            # Fetch failed — snap the selector back to match displayed comments.
            if self._source_state.belongs_to(current_song):
                self._platform_selector.blockSignals(True)
                try:
                    previous_idx = self._platform_selector.findData(
                        self._source_state.current_source_id
                    )
                    if previous_idx >= 0:
                        self._platform_selector.setCurrentIndex(previous_idx)
                finally:
                    self._platform_selector.blockSignals(False)
            return
        finally:
            self._platform_selector.setEnabled(True)

        # Only apply the result if the song hasn't changed in the meantime.
        if not self._source_state.belongs_to(current_song):
            return

        reader = create_reader(comments)
        self._comment_list.setModel(CommentListModel(reader))
        self._source_state.set_current_source(source_id)


class NowplayingSimilarSongsView(RefreshOnSongChangedMixin, SongMiniCardListView):
    def __init__(self, app: "GuiApp", parent=None):
        self._app = app
        super().__init__(parent=parent, no_scroll_v=False)
        self.setItemDelegate(
            SongMiniCardListDelegate(
                self,
                card_min_width=200,
                card_height=40,
                card_padding=(5 + SongMiniCardListDelegate.img_padding, 5, 0, 5),
                card_right_spacing=10,
                hover_color_role=QPalette.ColorRole.Base,
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
        kwargs.setdefault("no_scroll_v", False)
        kwargs.setdefault("row_height", 60)
        super().__init__(app, parent=parent, **kwargs)

        delegate = SongMiniCardListDelegate(
            self,
            card_min_width=200,
            card_height=40,
            card_padding=(5 + SongMiniCardListDelegate.img_padding, 5, 0, 5),
            card_right_spacing=10,
            hover_color_role=QPalette.ColorRole.Base,
        )
        self.setItemDelegate(delegate)
