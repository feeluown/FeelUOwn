from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QModelIndex, QItemSelectionModel, QRectF
from PyQt6.QtGui import QPainter, QPalette
from PyQt6.QtWidgets import QMenu, QAbstractItemView

from feeluown.utils.aio import run_fn, run_afn
from feeluown.library import (
    BriefSongModel,
    SupportsCurrentUserDislikeAddSong,
    SupportsCurrentUser,
)
from feeluown.player import PlaylistMode
from feeluown.gui.components import SongMenuInitializer
from feeluown.gui.helpers import fetch_cover_wrapper
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListView,
    SongMiniCardListModel,
    SongMiniCardListDelegate,
)
from feeluown.i18n import t
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
        # PlayerPlaylistModel mirrors the live playback queue. It must not keep
        # a partially fetched _items list because playlist.songs_removed emits
        # ranges from the full queue; a shorter _items list would make Qt's
        # remove notification handlers index past the local cache.
        self._items = list(playlist.list())
        self._playlist.songs_added.connect(self.on_songs_added)
        self._playlist.songs_removed.connect(self.on_songs_removed)
        self._playlist.songs_reordered.connect(self.on_songs_reordered)

    # Disable ReaderFetchMoreMixin for the live playback queue. The model rows
    # are driven by playlist signals instead of reader pagination.
    def can_fetch_more(self, _=None):
        return False

    def canFetchMore(self, _):
        return False

    def fetchMore(self, _):
        return None

    def flags(self, index):
        flags = super().flags(index)
        song = index.data(Qt.ItemDataRole.UserRole)[0]
        if self._playlist.is_bad(song):
            # Disable bad song.
            flags &= ~Qt.ItemFlag.ItemIsEnabled
        return flags

    def on_songs_added(self, index, count):
        if count <= 0:
            return
        if index < 0 or index > len(self._items):
            self._reset_from_playlist()
            return
        if index + count > len(self._playlist.list()):
            self._reset_from_playlist()
            return
        self.beginInsertRows(QModelIndex(), index, index + count - 1)
        # Insert from tail to front.
        while count > 0:
            self._items.insert(index, self._playlist[index + count - 1])
            count -= 1
        self.endInsertRows()

    def on_songs_removed(self, index, count):
        if count <= 0:
            return
        if index < 0 or index + count > len(self._items):
            self._reset_from_playlist()
            return
        self.beginRemoveRows(QModelIndex(), index, index + count - 1)
        while count > 0:
            self._items.pop(index + count - 1)
            count -= 1
        self.endRemoveRows()

    def on_songs_reordered(self, index, count):
        self._reset_from_playlist()

    def _reset_from_playlist(self):
        self.beginResetModel()
        self._items = list(self._playlist.list())
        self.image_cache.clear()
        self._image_colors.clear()
        self._image_fetching.clear()
        self.endResetModel()


class FMCandidatePlaylistDelegate(SongMiniCardListDelegate):
    def __init__(self, app: "GuiApp", view, *args, **kwargs):
        super().__init__(view, *args, **kwargs)
        self._app = app

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if self.is_fm_candidate(index):
            self._paint_candidate_badge(painter, option)

    def is_fm_candidate(self, index) -> bool:
        if not index.isValid():
            return False
        playlist = self._app.playlist
        if playlist.mode is not PlaylistMode.fm:
            return False
        row = index.row()
        songs = playlist.list()
        if not 0 <= row < len(songs):
            return False
        current_row = playlist.current_song_index()
        return current_row is None or row > current_row

    def _paint_candidate_badge(self, painter, option):
        text = t("fm-candidate-badge")
        painter.save()
        font = painter.font()
        pixel_size = font.pixelSize()
        if pixel_size > 0:
            font.setPixelSize(max(9, pixel_size - 2))
        painter.setFont(font)
        text_width = painter.fontMetrics().horizontalAdvance(text)
        rect = option.rect
        item_width, _ = self.item_sizehint()
        bg_width = min(
            rect.width() - self.card_left_padding - self.card_right_spacing,
            item_width,
        )
        badge_width = max(22, text_width + 12)
        badge_rect = QRectF(
            rect.x() + self.card_left_padding + bg_width - badge_width - 6,
            rect.y() + self.card_top_padding + 5,
            badge_width,
            14,
        )
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        color = option.palette.color(QPalette.ColorRole.Highlight)
        color.setAlpha(90)
        painter.setBrush(color)
        painter.drawRoundedRect(badge_rect, 7, 7)
        painter.setPen(option.palette.color(QPalette.ColorRole.HighlightedText))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()


class PlayerPlaylistView(SongMiniCardListView):
    _model = None

    def __init__(self, app: "GuiApp", *args, **kwargs):
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

        songs = [index.data(Qt.ItemDataRole.UserRole)[0] for index in indexes]
        menu = QMenu()
        if self._app.playlist.mode is PlaylistMode.fm:
            btn_text = t("fm-radio-current-song-dislike")
        else:
            btn_text = t("track-playlist-remove")
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
                action_dislike = menu.addAction(t("track-provider-blacklist-add"))
                action_dislike.triggered.connect(
                    lambda: run_afn(self._dislike_and_remove_songs, songs)
                )

        if len(songs) == 1:
            menu.addSeparator()
            SongMenuInitializer(self._app, songs[0]).apply(menu)
        menu.exec(e.globalPos())

    def scroll_to_current_song(
        self,
        hint=QAbstractItemView.ScrollHint.PositionAtCenter,
    ):
        """Scroll to the current song, and select it to highlight it."""
        current_song = self._app.playlist.current_song
        songs = self._app.playlist.list()
        if current_song is not None and current_song in songs:
            model = self.model()
            row = songs.index(current_song)
            index = model.index(row, 0)
            # In order to highlight the current song.
            self.selectionModel().select(
                index, QItemSelectionModel.SelectionFlag.SelectCurrent
            )
            self.scrollTo(index, hint)

    async def _dislike_and_remove_songs(self, songs):
        song: BriefSongModel = songs[0]
        provider = self._app.library.get(song.source)
        assert isinstance(provider, SupportsCurrentUserDislikeAddSong)
        self._app.show_msg(t("track-provider-blacklist-adding"), timeout=3000)
        ok = await run_fn(provider.current_user_dislike_add_song, song)
        if ok:
            self._app.show_msg(t("track-provider-blacklist-add-succ"))
        else:
            self._app.show_msg(t("track-provider-blacklist-add-fail"), timeout=3000)
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
                self._app.show_msg(
                    t("track-radio-mode-remove-latest"),
                    timeout=3000,
                )
                self._app.playlist.next()
            else:
                self._app.playlist.remove(song)
