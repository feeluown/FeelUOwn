from typing import TYPE_CHECKING
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
from feeluown.library import (
    SongStandbyOptions,
    SupportsSongHotComments,
    SupportsSongSimilar,
)
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


class CommentStandbyManager:
    def __init__(self):
        self._song = None
        self._songs = []
        self._current_song_id = None

    @property
    def song(self):
        return self._song

    @property
    def current_song_id(self):
        return self._current_song_id

    def reset(self, song=None):
        self._song = song
        self._songs = []
        self._current_song_id = None
        if song is not None:
            self._songs = [song]
            self._current_song_id = self.get_song_id(song)

    def add_standby_songs(self, standbys):
        if self._song is None:
            return
        self._songs = [self._song]
        self._songs.extend(standbys)

    @staticmethod
    def get_song_id(song):
        return (song.source, song.identifier)

    def songs(self):
        return self._songs

    def has_standby(self):
        if self._song is None:
            return False
        return len(self._songs) > 1

    def get_song(self, song_id):
        for song in self._songs:
            if self.get_song_id(song) == song_id:
                return song
        return None

    def set_current_song(self, song):
        self._current_song_id = self.get_song_id(song)


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

        self._comment_source_selector = QComboBox(self)
        self._comment_source_selector.setSizeAdjustPolicy(
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
        self._layout.addWidget(self._comment_source_selector)
        self._layout.addWidget(self._comment_list)

        self._comment_source_selector.hide()
        self._comment_source_selector.currentIndexChanged.connect(
            lambda idx: self._app.task_mgr.run_afn_preemptive(
                self._on_comment_source_changed, idx
            )
        )

        self._comment_standby_manager = CommentStandbyManager()

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
            self._comment_source_selector.hide()
            self._comment_standby_manager.reset()
            return

        self._comment_standby_manager.reset(song)

        # Load current platform comments.
        reader = create_reader([])
        provider = self._app.library.get(song.source)
        if isinstance(provider, SupportsSongHotComments):
            comments = await run_fn(provider.song_list_hot_comments, song)
            reader = create_reader(comments)
        self._comment_list.setModel(CommentListModel(reader))

        # Find matching songs on other platforms that support hot comments.
        # Reset state and hide the selector before the async search so
        # stale entries from the previous song are not shown in the interim.
        self._comment_source_selector.hide()
        standbys = await self._find_standby_songs(song)
        self._comment_standby_manager.add_standby_songs(standbys)
        self._update_comment_source_selector()

    async def _find_standby_songs(self, song):
        """Search all providers for the same song.

        Returns the matched BriefSongModel list.
        Only includes providers that support hot comments.
        """
        # Only search providers that can supply comments for the matched song.
        comment_providers = {
            p.identifier
            for p in self._app.library.list()
            if p.identifier != song.source
            and isinstance(p, SupportsSongHotComments)
        }
        if not comment_providers:
            return []

        try:
            return await self._app.library.a_list_song_standby_v3(
                song,
                SongStandbyOptions(
                    source_in=list(comment_providers),
                    limit_per_source=3,
                ),
            )
        except Exception:
            logger.exception("Standby song search failed")

        return []

    @staticmethod
    def _format_comment_source_label(provider_name, song):
        title = song.title or song.identifier
        if song.artists_name:
            return f"{provider_name} · {title} - {song.artists_name}"
        return f"{provider_name} · {title}"

    def _update_comment_source_selector(self):
        self._comment_source_selector.blockSignals(True)
        try:
            self._comment_source_selector.clear()

            for candidate in self._comment_standby_manager.songs():
                provider = self._app.library.get(candidate.source)
                provider_name = provider.name if provider else candidate.source
                label = self._format_comment_source_label(provider_name, candidate)
                self._comment_source_selector.addItem(
                    label,
                    self._comment_standby_manager.get_song_id(candidate),
                )

            self._comment_source_selector.setVisible(
                self._comment_standby_manager.has_standby()
            )
            self._comment_source_selector.setCurrentIndex(0)
        finally:
            self._comment_source_selector.blockSignals(False)

    async def _on_comment_source_changed(self, index):
        if index < 0:
            return
        song_id = self._comment_source_selector.itemData(index)
        if song_id == self._comment_standby_manager.current_song_id:
            return

        song = self._comment_standby_manager.get_song(song_id)
        if song is None:
            return
        provider = self._app.library.get(song.source)
        if not isinstance(provider, SupportsSongHotComments):
            return

        # Disable the selector during the fetch — keep the current comments
        # visible so there's no flicker and they're not lost on failure.
        self._comment_source_selector.setEnabled(False)
        try:
            comments = await run_fn(provider.song_list_hot_comments, song)
        except Exception:
            # Fetch failed — snap the selector back to match displayed comments.
            self._comment_source_selector.blockSignals(True)
            try:
                previous_idx = self._comment_source_selector.findData(
                    self._comment_standby_manager.current_song_id
                )
                if previous_idx >= 0:
                    self._comment_source_selector.setCurrentIndex(previous_idx)
            finally:
                self._comment_source_selector.blockSignals(False)
            return
        finally:
            self._comment_source_selector.setEnabled(True)

        reader = create_reader(comments)
        self._comment_list.setModel(CommentListModel(reader))
        self._comment_standby_manager.set_current_song(song)


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
