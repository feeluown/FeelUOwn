import asyncio
import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFontMetrics, QPalette, QColor, QPainter
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QStackedLayout, QVBoxLayout, QWidget

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

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


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

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)

        self._source_combo = QComboBox(self)
        self._source_combo.currentIndexChanged.connect(
            lambda idx: run_afn(self._on_source_changed, idx)
        )
        self._layout.addWidget(self._source_combo)

        source_name_map = {
            pvd.identifier: pvd.name for pvd in self._app.library.list()
        }
        self._list_view = CommentListView(
            parent=self,
            no_scroll_v=False,
            delegate_options={
                "quoted_bg_color_role": QPalette.ColorRole.Base,
                "source_name_map": source_name_map,
            },
        )
        self._layout.addWidget(self._list_view)

        self._current_song = None
        self._matches: dict[str, object] = {}
        self._source_fetch_task = None
        self._refresh_gen = 0

    def viewport(self):
        # Shim: nowplaying_overlay.py calls comments_view.viewport().
        return self._list_view.viewport()

    async def refresh(self):
        song = self._app.playlist.current_song
        self._current_song = song
        self._matches = {}
        self._refresh_gen += 1
        gen = self._refresh_gen

        if self._source_fetch_task is not None and not self._source_fetch_task.done():
            self._source_fetch_task.cancel()

        self._source_combo.blockSignals(True)
        self._source_combo.clear()

        if song is None:
            self._list_view.setModel(CommentListModel(create_reader([])))
            self._source_combo.blockSignals(False)
            return

        self._source_combo.addItem(t("track-comments-source-current"), song.source)
        self._source_combo.blockSignals(False)
        await self._fetch_and_show_comments(song.source, song, gen)

        # Search for matches on other providers.
        await self._search_other_sources(song, gen)

    async def _fetch_and_show_comments(self, provider_id, song, expected_gen=None):
        if expected_gen is not None and expected_gen != self._refresh_gen:
            return
        provider = self._app.library.get(provider_id)
        if provider is not None and isinstance(provider, SupportsSongHotComments):
            try:
                comments = await run_fn(provider.song_list_hot_comments, song)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Failed to load comments from %s", provider_id)
                comments = []
            comments = comments or []
            if expected_gen is not None and expected_gen != self._refresh_gen:
                return
            # Guard against the user having switched to a different source.
            if self._source_combo.currentData() != provider_id:
                return
            patched_comments = []
            for c in comments:
                if not c.source or c.source == "dummy":
                    c = c.model_copy(update={"source": provider_id})
                patched_comments.append(c)
            # Refresh source name map in case providers were added dynamically.
            self._list_view.set_source_name_map({
                pvd.identifier: pvd.name for pvd in self._app.library.list()
            })
            self._list_view.setModel(CommentListModel(create_reader(patched_comments)))
        else:
            if self._source_combo.currentData() != provider_id:
                return
            self._list_view.setModel(CommentListModel(create_reader([])))

    async def _search_other_sources(self, song, expected_gen=None):
        try:
            matches = await self._app.library.a_search_song_matches(song)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Failed to search song matches for comments")
            return

        if expected_gen is not None and expected_gen != self._refresh_gen:
            return

        valid_matches = []
        for pid, matched_song, _ in matches:
            provider = self._app.library.get(pid)
            if provider is not None and isinstance(provider, SupportsSongHotComments):
                valid_matches.append((pid, matched_song))

        if not valid_matches:
            return

        if expected_gen is not None and expected_gen != self._refresh_gen:
            return

        # Also guard against the song having changed to a different track.
        current = self._app.playlist.current_song
        if current is None or current.source != song.source or current.identifier != song.identifier:
            return

        self._source_combo.blockSignals(True)
        for pid, matched_song in valid_matches:
            self._matches[pid] = matched_song
            provider = self._app.library.get(pid)
            name = provider.name if provider else pid
            self._source_combo.addItem(name, pid)
        self._source_combo.blockSignals(False)

    async def _on_source_changed(self, index):
        if index < 0:
            return
        if self._current_song is None:
            return
        provider_id = self._source_combo.itemData(index)
        if provider_id == self._current_song.source:
            song = self._current_song
        else:
            song = self._matches.get(provider_id)
        if song is not None:
            if self._source_fetch_task is not None and not self._source_fetch_task.done():
                self._source_fetch_task.cancel()
            task = run_afn(self._fetch_and_show_comments, provider_id, song, self._refresh_gen)
            self._source_fetch_task = task
            try:
                await task
            except asyncio.CancelledError:
                pass


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
