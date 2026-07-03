import logging
import time
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlparse

from PyQt6.QtCore import QEvent, QMargins, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QFont,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPalette,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from feeluown.ai import SongSuggestion
from feeluown.app.gui_app import GuiApp
from feeluown.gui.components.search import create_search_result_view
from feeluown.gui.helpers import IS_MACOS, secondary_text_color
from feeluown.gui.widgets import PlayButton, PlusButton
from feeluown.gui.widgets.textbtn import TextButton
from feeluown.gui.widgets.header import MidHeader
from feeluown.gui.components.dynamic_island import DynamicIslandStatusBar
from feeluown.gui.widgets.ai_chat import (
    ChatHistoryWidget,
    ChatInputWidget,
    SurfaceRadius,
    draw_round_surface,
    surface_border_color,
)
from feeluown.gui.components.player_playlist import (
    PlayerPlaylistView,
    FMCandidatePlaylistDelegate,
)
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListDelegate,
)
from feeluown.gui.components.overlay import AppOverlayContainer, AppOverlayOptions
from feeluown.library import BriefSongModel, ModelState, ResolveFailed, parse_line
from feeluown.i18n import t
from feeluown.utils import aio

logger = logging.getLogger(__name__)


def _create_titlebar_mode(app):
    if not IS_MACOS:
        return None
    from feeluown.gui.macos_titlebar import MacOSNativeTitlebarMode

    return MacOSNativeTitlebarMode(app)


@dataclass
class ParsedSongLink:
    kind: str
    model: SongSuggestion | BriefSongModel
    url: str


def _song_suggestion_to_display_song(
    suggestion: SongSuggestion, identifier: str
) -> BriefSongModel:
    return BriefSongModel(
        state=ModelState.not_exists,
        source="ai",
        identifier=identifier,
        title=suggestion.title,
        artists_name=suggestion.artists_name,
    )


def song_suggestion_to_markdown_url(suggestion: SongSuggestion) -> str:
    query = urlencode({"title": suggestion.title, "artists": suggestion.artists_name})
    return f"fuo://song-suggestion?{query}"


def parse_song_link(url: str):
    parsed_link = parse_song_link_info(url)
    return parsed_link.model if parsed_link is not None else None


def parse_song_link_info(url: str):
    parsed = urlparse(url)
    if parsed.scheme != "fuo":
        return None

    query = parse_qs(parsed.query)
    if parsed.netloc in ("song-suggestion", "ai-song"):
        title = query.get("title", [""])[0].strip()
        artists_name = query.get("artists", [""])[0].strip()
        if title:
            return ParsedSongLink(
                kind="suggestion",
                model=SongSuggestion(
                    title=title,
                    artists_name=artists_name,
                    description="",
                ),
                url=url,
            )
    elif parsed.netloc == "song":
        source = query.get("source", [""])[0].strip()
        identifier = query.get("identifier", [""])[0].strip()
        title = query.get("title", [""])[0].strip()
        artists_name = query.get("artists", [""])[0].strip()
        if source and identifier:
            return ParsedSongLink(
                kind="resource",
                model=BriefSongModel(
                    source=source,
                    identifier=identifier,
                    title=title,
                    artists_name=artists_name,
                ),
                url=url,
            )
    else:
        try:
            model, path = parse_line(url)
        except (ResolveFailed, ValueError):
            return None
        if path == "" and isinstance(model, BriefSongModel):
            return ParsedSongLink(kind="resource", model=model, url=url)
    return None


class SongSuggestionItemWidget(QWidget):
    row_height = 56
    _palette_ready = False

    def __init__(self, song: BriefSongModel, list_view: QListWidget):
        parent = list_view
        super().__init__(parent=parent)
        self._palette_ready = False
        self.song = song
        self._list_view = list_view
        self._hovered = False
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(self.row_height)

        self._title_label = QLabel(song.title_display, self)
        self._title_label.setWordWrap(False)
        self._artist_label = QLabel(song.artists_name_display, self)
        self._artist_label.setWordWrap(False)
        artist_font = self._artist_label.font()
        artist_font.setPixelSize(max(10, artist_font.pixelSize() - 1))
        self._artist_label.setFont(artist_font)

        self.play_btn = PlayButton(length=24, padding=0.3)
        self.add_btn = PlusButton(length=24, padding=0.3)
        self.play_btn.setToolTip(t("ai-chat-link-play"))
        self.add_btn.setToolTip(t("add-to-playlist"))
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.addWidget(self._title_label)
        text_layout.addWidget(self._artist_label)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(2)
        button_layout.addWidget(self.play_btn)
        button_layout.addWidget(self.add_btn)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 8, 6)
        layout.setSpacing(8)
        layout.addLayout(text_layout, 1)
        layout.addLayout(button_layout)
        self._palette_ready = True
        self._apply_palette()

    def _apply_palette(self):
        if not self._palette_ready:
            return
        pal = QPalette(QGuiApplication.palette())
        secondary = secondary_text_color(pal)
        pal.setColor(QPalette.ColorRole.WindowText, secondary)
        pal.setColor(QPalette.ColorRole.Text, secondary)
        self._artist_label.setPalette(pal)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        current_item = self._list_view.currentItem()
        current = (
            current_item is not None
            and self._list_view.itemWidget(current_item) is self
        )
        if current or self._hovered:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            color = self.palette().color(QPalette.ColorRole.Highlight)
            color.setAlpha(42 if current else 24)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(
                QRectF(self.rect()).adjusted(2, 2, -2, -2),
                SurfaceRadius,
                SurfaceRadius,
            )
            painter.end()
        super().paintEvent(event)


class AIArtifactSongListView(QListWidget):
    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._suggestion_by_display_song = {}
        self._radius = SurfaceRadius
        self.setMinimumWidth(280)
        self.setMaximumWidth(360)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setMouseTracking(True)
        self.setSpacing(4)
        self.setStyleSheet(
            """
            AIArtifactSongListView {
                background: transparent;
                border: 0;
                outline: none;
            }
            AIArtifactSongListView::item {
                background: transparent;
            }
            """
        )
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.currentItemChanged.connect(self._on_current_item_changed)

    def set_artifact(self, artifact):
        self.clear()
        self._suggestion_by_display_song = {}
        for index, song in enumerate(artifact.songs):
            if isinstance(song, SongSuggestion):
                display_song = _song_suggestion_to_display_song(
                    song, f"{artifact.identifier}-{index}"
                )
                self._suggestion_by_display_song[display_song] = song
            else:
                display_song = song

            list_item = QListWidgetItem(self)
            list_item.setData(Qt.ItemDataRole.UserRole, display_song)
            list_item.setSizeHint(QSize(260, SongSuggestionItemWidget.row_height))
            self.addItem(list_item)
            item_widget = SongSuggestionItemWidget(display_song, self)
            item_widget.play_btn.clicked.connect(
                lambda _checked=False, song=display_song: self._play_display_song(song)
            )
            item_widget.add_btn.clicked.connect(
                lambda _checked=False, song=display_song: aio.run_afn(
                    self._add_display_song, song
                )
            )
            self.setItemWidget(list_item, item_widget)

    def paintEvent(self, event):
        draw_round_surface(self.viewport(), self._radius, QPalette.ColorRole.Base)
        super().paintEvent(event)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos()) or self.currentItem()
        if item is None:
            return

        self.setCurrentItem(item)
        song = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        action = menu.addAction(t("ai-chat-link-search"))
        action.setObjectName("ai-chat-link-search")
        action.triggered.connect(lambda: self._show_search(song))
        action = menu.addAction(t("ai-chat-link-play"))
        action.setObjectName("ai-chat-link-play")
        action.triggered.connect(lambda: self._play_display_song(song))
        action = menu.addAction(t("add-to-playlist"))
        action.setObjectName("ai-chat-link-add-to-playlist")
        action.triggered.connect(lambda: aio.run_afn(self._add_display_song, song))
        menu.exec(event.globalPos())

    def _on_item_double_clicked(self, item):
        song = item.data(Qt.ItemDataRole.UserRole)
        if song is not None:
            self._play_display_song(song)

    def _on_current_item_changed(self, current, previous):
        for item in (current, previous):
            if item is not None:
                widget = self.itemWidget(item)
                if widget is not None:
                    widget.update()

    def _show_search(self, song: BriefSongModel):
        view = create_search_result_view(self._app, song)
        view.show()

    def _play_display_song(self, song: BriefSongModel):
        aio.run_afn(self._match_and_play, song)

    async def _match_and_play(self, song: BriefSongModel):
        matched = await self._match_display_song(song)
        if matched is None:
            self._show_search(song)
            self._app.show_msg(t("ai-chat-song-match-failed"))
            return
        self._app.playlist.play_model(matched)

    async def _add_display_song(self, song: BriefSongModel):
        matched = await self._match_display_song(song)
        if matched is None:
            self._show_search(song)
            self._app.show_msg(t("ai-chat-song-match-failed"))
            return
        self._app.playlist.add(matched)

    async def _match_display_song(self, song: BriefSongModel):
        suggestion = self._suggestion_by_display_song.get(song)
        if suggestion is None:
            return song
        return await self._app.ai.get_copilot().match_song_suggestion(suggestion)


class AIArtifactSidebar(QWidget):
    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._song_list_view = AIArtifactSongListView(app, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._song_list_view, 1)

    def set_artifact(self, artifact):
        self._song_list_view.set_artifact(artifact)


def _apply_surface_palette(widget, color):
    pal = QPalette(QGuiApplication.palette())
    for group in (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    ):
        pal.setColor(group, QPalette.ColorRole.Window, color)
        pal.setColor(group, QPalette.ColorRole.Base, color)
    widget.setPalette(pal)
    widget.setAutoFillBackground(True)


def _apply_transparent_surface_palette(widget, color):
    _apply_surface_palette(widget, color)
    widget.setAutoFillBackground(False)


def _apply_scroll_surface_palette(widget, color):
    _apply_surface_palette(widget, color)
    viewport = widget.viewport()
    viewport.setPalette(widget.palette())
    viewport.setAutoFillBackground(True)


def _connect_theme_changed(theme_mgr, receiver):
    try:
        theme_mgr.theme_changed.connect(receiver, weak=False)
    except TypeError:
        theme_mgr.theme_changed.connect(receiver)


class DraggableToolbar(QWidget):
    def mousePressEvent(self, event):
        window = self._window_handle()
        if event.button() == Qt.MouseButton.LeftButton and window is not None:
            if window.startSystemMove():
                event.accept()
                return
        super().mousePressEvent(event)

    def _window_handle(self):
        return self.window().windowHandle()


class ToolbarSeparator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(1)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        color = surface_border_color(self.palette(), QPalette.ColorRole.Base)
        painter.fillRect(QRectF(self.rect()), color)
        painter.end()


class SidebarPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setAutoFillBackground(False)

    def paintEvent(self, event):
        draw_round_surface(self, SurfaceRadius)
        super().paintEvent(event)


class SidebarShadow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedWidth(10)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        shadow = self.palette().color(QPalette.ColorRole.Shadow)
        shadow.setAlpha(38)
        transparent = shadow
        transparent.setAlpha(0)
        gradient.setColorAt(0.0, transparent)
        gradient.setColorAt(0.65, transparent)
        gradient.setColorAt(1.0, shadow)
        painter.fillRect(QRectF(self.rect()), gradient)
        painter.end()


class AIChatBox(QWidget):
    """A lightweight AI assistant UI."""

    artifact_added = pyqtSignal(object)
    working_state_changed = pyqtSignal(bool)
    playlist_sidebar_requested = pyqtSignal()

    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app
        self.copilot = self._app.ai.get_copilot()

        self.history_widget = ChatHistoryWidget(self)
        self._dynamic_island = DynamicIslandStatusBar(app)
        self.input_widget = ChatInputWidget(
            self,
            status_widget=self._dynamic_island,
        )
        self._collecting_artifacts = False
        self._pending_artifacts = []

        self.input_widget.send_clicked.connect(
            lambda q: aio.run_afn_ref(self.exec_user_query, q)
        )
        self.working_state_changed.connect(self.on_working_state_changed)
        self.artifact_added.connect(self.on_artifact_added)
        self.copilot.working_state_changed.connect(
            self.working_state_changed.emit,
            weak=False,
        )
        self.copilot.artifact_added.connect(
            self.artifact_added.emit,
            weak=False,
        )
        self._app.playlist.mode_changed.connect(self._refresh_context)
        self.setup_ui()
        self._refresh_context()

    def setup_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.history_widget)
        layout.addWidget(self.input_widget)

    async def exec_user_query(self, query: str):
        self.history_widget.add_message("user", query)
        self.history_widget.scroll_to_bottom()

        status_card = self.history_widget.add_streaming_status(
            t("ai-chat-stream-thinking")
        )
        current_label = None
        response_message = ""
        last_update_ts = time.time()
        seen_tool = False
        pre_tool_stream_threshold = 16
        failed = False
        self._collecting_artifacts = True
        self._pending_artifacts = []

        try:
            async for token, metadata in self.copilot.astream_user_query(query):
                node = metadata["langgraph_node"]
                if node == "model":
                    status_card.set_status(t("ai-chat-stream-writing"))
                    for block in token.content_blocks:
                        if block["type"] == "text":
                            response_message += block["text"]

                    if (
                        current_label is None
                        and (seen_tool or len(response_message.strip()) >=
                             pre_tool_stream_threshold)
                    ):
                        current_label = self.history_widget.create_message_label(
                            "assistant", ""
                        )
                        self.history_widget.move_history_widget_to_bottom(status_card)
                    if current_label is not None and last_update_ts + 0.2 <= time.time():
                        current_label.setText(response_message)
                        self.history_widget.scroll_to_bottom()
                        last_update_ts = time.time()
                elif node == "tools":
                    status_card.set_status(
                        t("ai-chat-stream-tool", tool=token.name)
                    )
                    if token.name.startswith(
                        ("ai_radio_", "fm_candidates_")
                    ):
                        self.playlist_sidebar_requested.emit()
                    if current_label is not None and response_message.strip():
                        current_label.set_markdown(response_message)
                    self.history_widget.add_tool_event(
                        t("ai-chat-tool-called", tool=token.name)
                    )
                    current_label = None
                    response_message = ""
                    seen_tool = True
        except Exception:
            logger.exception("exec_user_query failed")
            failed = True
            if current_label is not None and response_message:
                current_label.setText(response_message)
            status_card.finish(t("ai-chat-stream-failed"))
        finally:
            self._collecting_artifacts = False

        if failed:
            self._flush_pending_artifacts()
            self.history_widget.scroll_to_bottom()
            return

        self.history_widget.remove_history_widget(status_card)

        # Final rendering: parse accumulated text as markdown
        if response_message.strip():
            if current_label is None:
                current_label = self.history_widget.create_message_label(
                    "assistant", ""
                )
            current_label.set_markdown(response_message)

        self._flush_pending_artifacts()
        self.history_widget.scroll_to_bottom()

    def on_new_thread_btn_clicked(self):
        self.copilot.new_thread()
        self._pending_artifacts = []
        self.history_widget.clear()

    def on_working_state_changed(self, working: bool):
        self.input_widget.enable_send(not working)

    def on_artifact_added(self, artifact):
        if self._collecting_artifacts:
            self._pending_artifacts.append(artifact)
        else:
            self.history_widget.add_artifact(artifact)

    def _flush_pending_artifacts(self):
        for artifact in self._pending_artifacts:
            self.history_widget.add_artifact(artifact)
        self._pending_artifacts = []

    def _get_active_ai_radio(self):
        return self._app.ai.get_active_radio()

    def _refresh_context(self, *_):
        if self._get_active_ai_radio() is not None:
            self.input_widget.set_placeholder(t("ai-radio-input-placeholder"))
        else:
            self.input_widget.set_placeholder(t("ai-chat-input-placeholder"))
        self.input_widget.set_msg("")


class Body(QWidget):
    def __init__(self, app: "GuiApp"):
        super().__init__(parent=None)
        self._app = app
        self._connected_ai_radio = None
        self._updating_palette = False
        self._palette_refresh_scheduled = False
        self._palette_ready = False
        self._header = MidHeader(t("ai-chat-header"))
        self._new_thread_btn = TextButton(t("ai-chat-new"), height=26)
        self._sidebar_btn = TextButton(t("ai-chat-open-sidebar"), height=26)
        self._collapse_btn = TextButton(t("fold-collapse"), height=26)
        self._chat_box = AIChatBox(app)
        self._playlist_sidebar = PlayerPlaylistView(
            self._app,
            row_height=60,
            no_scroll_v=False,
        )
        self._playlist_sidebar.setMinimumWidth(280)
        self._playlist_sidebar.setMaximumWidth(360)
        self._playlist_sidebar.setItemDelegate(
            FMCandidatePlaylistDelegate(
                self._app,
                self._playlist_sidebar,
                card_min_width=260,
                card_height=40,
                card_padding=(5 + SongMiniCardListDelegate.img_padding, 5, 0, 5),
                card_right_spacing=10,
            )
        )
        self._artifact_sidebar = AIArtifactSidebar(self._app)
        self._right_sidebar_stack = QStackedWidget(self)
        self._right_sidebar_stack.setMinimumWidth(280)
        self._right_sidebar_stack.setMaximumWidth(360)
        self._right_sidebar_stack.addWidget(self._playlist_sidebar)
        self._right_sidebar_stack.addWidget(self._artifact_sidebar)
        self._sidebar_panel = SidebarPanel(self)
        self._sidebar_panel.setMinimumWidth(300)
        self._sidebar_panel.setMaximumWidth(380)
        self._sidebar_header = QLabel(t("playlist"))
        self._sidebar_status_label = QLabel("")
        self._sidebar_status_label.setWordWrap(True)
        self._sidebar_status_label.hide()
        header_font = self._sidebar_header.font()
        header_font.setPixelSize(13)
        header_font.setWeight(QFont.Weight.DemiBold)
        self._sidebar_header.setFont(header_font)
        self._sidebar_header.setStyleSheet("padding: 0 2px;")
        self._sidebar_layout = QVBoxLayout(self._sidebar_panel)
        self._sidebar_layout.setContentsMargins(12, 10, 12, 12)
        self._sidebar_layout.setSpacing(8)
        self._sidebar_layout.addWidget(self._sidebar_header)
        self._sidebar_layout.addWidget(self._right_sidebar_stack, 1)
        self._sidebar_layout.addWidget(self._sidebar_status_label)
        self._sidebar_panel.hide()
        self._sidebar_shadow = SidebarShadow(self)
        self._sidebar_shadow.hide()

        self._new_thread_btn.clicked.connect(self._chat_box.on_new_thread_btn_clicked)
        self._sidebar_btn.clicked.connect(self.toggle_sidebar)
        self._collapse_btn.clicked.connect(self._collapse_overlay)
        self._chat_box.playlist_sidebar_requested.connect(self.show_playlist_sidebar)
        self._chat_box.history_widget.artifact_clicked.connect(self.show_artifact)
        self._chat_box.history_widget.link_activated.connect(self._on_link_activated)
        self._chat_box.history_widget.link_context_menu_requested.connect(
            self._on_link_context_menu_requested
        )
        self._app.playlist.mode_changed.connect(self._refresh_context)

        self._layout = QVBoxLayout(self)
        if IS_MACOS:
            self._layout.setContentsMargins(86, 10, 10, 10)
        else:
            self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(10)
        self._toolbar = DraggableToolbar(self)
        self._toolbar_separator = ToolbarSeparator(self)
        self._toolbar_layout = QHBoxLayout(self._toolbar)
        self._content_layout = QHBoxLayout()
        self._toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self._toolbar_layout.addWidget(self._header)
        self._toolbar_layout.addStretch(0)
        self._toolbar_layout.addWidget(self._new_thread_btn)
        self._toolbar_layout.addWidget(self._sidebar_btn)
        self._toolbar_layout.addWidget(self._collapse_btn)

        self.setAutoFillBackground(True)
        self._apply_palette()
        self._playlist_sidebar.setAutoFillBackground(False)
        self._playlist_sidebar.viewport().setAutoFillBackground(False)
        self._playlist_sidebar.setStyleSheet(
            """
            PlayerPlaylistView {
                background: transparent;
                outline: none;
                border: 0;
            }
            PlayerPlaylistView::item:selected,
            PlayerPlaylistView::item:hover {
                background: transparent;
            }
            """
        )
        for btn in (self._new_thread_btn, self._sidebar_btn, self._collapse_btn):
            btn.setStyleSheet("border-radius: 8px;")

        self._content_layout.addWidget(self._chat_box)
        self._content_layout.addWidget(self._sidebar_shadow)
        self._content_layout.addWidget(self._sidebar_panel)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._content_layout.setStretch(0, 1)
        self._content_layout.setStretch(1, 0)
        self._content_layout.setStretch(2, 0)
        self._layout.addWidget(self._toolbar)
        self._layout.addWidget(self._toolbar_separator)
        self._layout.addLayout(self._content_layout, 1)
        self.setAutoFillBackground(True)
        self._refresh_context()
        self._palette_ready = True
        self._apply_palette()
        _connect_theme_changed(self._app.theme_mgr, self._on_theme_changed)
        self._apply_palette()

    def _on_theme_changed(self, _theme):
        self._schedule_palette_refresh(force=True)

    def _schedule_palette_refresh(self, force=False):
        if not self._palette_ready:
            return
        if self._palette_refresh_scheduled and not force:
            return
        self._palette_refresh_scheduled = True
        self._apply_palette()
        QTimer.singleShot(0, self._apply_scheduled_palette)

    def _apply_scheduled_palette(self):
        self._palette_refresh_scheduled = False
        self._apply_palette()

    def _apply_palette(self):
        if not self._palette_ready:
            return
        if self._updating_palette:
            return
        self._updating_palette = True
        try:
            app_pal = QPalette(QGuiApplication.palette())
            base_color = app_pal.color(QPalette.ColorRole.Base)
            window_color = app_pal.color(QPalette.ColorRole.Window)

            body_pal = QPalette(app_pal)
            for group in (
                QPalette.ColorGroup.Active,
                QPalette.ColorGroup.Inactive,
                QPalette.ColorGroup.Disabled,
            ):
                body_pal.setColor(group, QPalette.ColorRole.Window, base_color)
                body_pal.setColor(group, QPalette.ColorRole.Base, base_color)
            self.setPalette(body_pal)

            _apply_transparent_surface_palette(
                self._right_sidebar_stack, window_color
            )
            _apply_transparent_surface_palette(self._sidebar_panel, window_color)
            _apply_surface_palette(self._artifact_sidebar, window_color)
            _apply_scroll_surface_palette(self._playlist_sidebar, window_color)
            _apply_scroll_surface_palette(
                self._artifact_sidebar._song_list_view, base_color
            )
            self._playlist_sidebar.setAutoFillBackground(False)
            self._playlist_sidebar.viewport().setAutoFillBackground(False)
            self._artifact_sidebar._song_list_view.setAutoFillBackground(False)
            self._artifact_sidebar._song_list_view.viewport().setAutoFillBackground(
                False
            )
            self._chat_box.history_widget._apply_palette()
            self._chat_box.input_widget._apply_palette()
            self._refresh_artist_labels()

            self._sidebar_status_label.setPalette(app_pal)
            self._sidebar_shadow.setPalette(body_pal)
            self.update()
            self._toolbar_separator.update()
            self._sidebar_panel.update()
            self._right_sidebar_stack.update()
            self._artifact_sidebar.update()
            self._artifact_sidebar._song_list_view.update()
            self._artifact_sidebar._song_list_view.viewport().update()
        finally:
            self._updating_palette = False

    def _refresh_artist_labels(self):
        for item_widget in self._artifact_sidebar._song_list_view.findChildren(
            SongSuggestionItemWidget
        ):
            item_widget._apply_palette()

    def toggle_sidebar(self):
        if (
            self._sidebar_panel.isVisible()
            and self._right_sidebar_stack.currentWidget() is self._playlist_sidebar
        ):
            self.set_sidebar_visible(False)
        else:
            self.set_sidebar_visible(True)

    def set_sidebar_visible(self, visible: bool):
        if visible:
            self.show_playlist_sidebar()
        else:
            self._sidebar_shadow.hide()
            self._right_sidebar_stack.hide()
            self._sidebar_panel.hide()

    def show_playlist_sidebar(self):
        self._right_sidebar_stack.setCurrentWidget(self._playlist_sidebar)
        self._sidebar_header.setText(t("playlist"))
        self._sync_sidebar_status_visibility()
        self._sidebar_shadow.show()
        self._right_sidebar_stack.show()
        self._sidebar_panel.show()
        self._playlist_sidebar.scroll_to_current_song(
            QAbstractItemView.ScrollHint.PositionAtTop
        )

    def show_artifact(self, artifact):
        self._artifact_sidebar.set_artifact(artifact)
        self._sidebar_header.setText(
            artifact.title or t("ai-chat-artifact-sidebar-title")
        )
        self._right_sidebar_stack.setCurrentWidget(self._artifact_sidebar)
        self._sync_sidebar_status_visibility()
        self._sidebar_shadow.show()
        self._right_sidebar_stack.show()
        self._sidebar_panel.show()

    def _on_link_activated(self, url: str):
        link = parse_song_link_info(url)
        if link is None:
            return
        if link.kind == "suggestion":
            self._show_link_search(link.model)
        else:
            aio.run_afn(self._play_link_model, link.model)

    def _on_link_context_menu_requested(self, url: str, global_pos):
        link = parse_song_link_info(url)
        if link is None:
            return

        menu = QMenu(self)
        model = link.model
        if link.kind == "suggestion":
            action = menu.addAction(t("ai-chat-link-search"))
            action.setObjectName("ai-chat-link-search")
            action.triggered.connect(lambda: self._show_link_search(model))
        action = menu.addAction(t("ai-chat-link-play"))
        action.setObjectName("ai-chat-link-play")
        action.triggered.connect(lambda: aio.run_afn(self._play_link_model, model))
        action = menu.addAction(t("add-to-playlist"))
        action.setObjectName("ai-chat-link-add-to-playlist")
        action.triggered.connect(lambda: aio.run_afn(self._add_link_model, model))
        menu.addSeparator()
        action = menu.addAction(t("ai-chat-link-copy"))
        action.setObjectName("ai-chat-link-copy")
        action.triggered.connect(lambda: QGuiApplication.clipboard().setText(url))
        menu.exec(global_pos)

    def _show_link_search(self, model):
        song = self._model_to_search_song(model)
        if song is None:
            return
        view = create_search_result_view(self._app, song)
        view.show()

    async def _play_link_model(self, model):
        song = await self._model_to_playable_song(model)
        if song is None:
            self._show_link_search(model)
            self._app.show_msg(t("ai-chat-song-match-failed"))
            return
        self._app.playlist.play_model(song)

    async def _add_link_model(self, model):
        song = await self._model_to_playable_song(model)
        if song is None:
            self._show_link_search(model)
            self._app.show_msg(t("ai-chat-song-match-failed"))
            return
        self._app.playlist.add(song)

    async def _model_to_playable_song(self, model):
        if isinstance(model, SongSuggestion):
            return await self._app.ai.get_copilot().match_song_suggestion(model)
        return model

    def _model_to_search_song(self, model):
        if isinstance(model, SongSuggestion):
            return _song_suggestion_to_display_song(
                model, song_suggestion_to_markdown_url(model)
            )
        return model

    def _collapse_overlay(self):
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, AppOverlayContainer):
                parent.hide()
                return
            parent = parent.parent()

    def _get_active_ai_radio(self):
        return self._app.ai.get_active_radio()

    def _refresh_context(self, *_):
        self._header.setText(t("ai-chat-header"))
        self._connect_ai_radio_status()
        self._sync_sidebar_status_visibility()

    def _connect_ai_radio_status(self):
        ai_radio = self._get_active_ai_radio()
        if ai_radio is self._connected_ai_radio:
            return
        if self._connected_ai_radio is not None:
            self._connected_ai_radio.status_changed.disconnect(
                self._on_ai_radio_status_changed
            )
        self._connected_ai_radio = ai_radio
        if ai_radio is not None:
            ai_radio.status_changed.connect(
                self._on_ai_radio_status_changed, weak=False
            )
            self._on_ai_radio_status_changed(ai_radio.status)
        else:
            self._on_ai_radio_status_changed("")

    def _on_ai_radio_status_changed(self, status):
        self._sidebar_status_label.setText(status)
        self._sync_sidebar_status_visibility()

    def _sync_sidebar_status_visibility(self):
        visible = (
            self._right_sidebar_stack.currentWidget() is self._playlist_sidebar
            and bool(self._sidebar_status_label.text())
        )
        self._sidebar_status_label.setVisible(visible)


class AIChatOverlay(AppOverlayContainer):
    def __init__(self, app: "GuiApp", body: Body, parent=None):
        super().__init__(
            app,
            body,
            parent=parent,
            options=AppOverlayOptions(
                margins=QMargins(0, 0, 0, 0),
                dim_background=False,
                close_on_focus_in=False,
            ),
        )
        self._titlebar_mode = _create_titlebar_mode(app)
        self._titlebar_reapply_scheduled = False
        self.body._schedule_palette_refresh(force=True)

    def showEvent(self, event):
        if self._titlebar_mode is not None:
            self._titlebar_mode.enter()
        super().showEvent(event)
        self.body._schedule_palette_refresh(force=True)

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._titlebar_mode is not None:
            self._titlebar_mode.exit()

    def eventFilter(self, obj, event):
        result = super().eventFilter(obj, event)
        if (
            self.isVisible()
            and obj == self._app
            and self._titlebar_mode is not None
            and event.type()
            in (QEvent.Type.Resize, QEvent.Type.WindowStateChange)
        ):
            self._schedule_titlebar_reapply()
        return result

    def _schedule_titlebar_reapply(self):
        if self._titlebar_reapply_scheduled:
            return
        self._titlebar_reapply_scheduled = True
        QTimer.singleShot(0, self._reapply_titlebar_mode)

    def _reapply_titlebar_mode(self):
        self._titlebar_reapply_scheduled = False
        if self.isVisible() and self._titlebar_mode is not None:
            self._titlebar_mode.reapply()


def create_aichat_overlay(app: "GuiApp", parent=None) -> AppOverlayContainer:
    """Create an overlay for the AI chat"""
    body = Body(app)
    return AIChatOverlay(app, body, parent=parent)


if __name__ == "__main__":
    from feeluown.gui.debug import mock_app, simple_layout

    with simple_layout(theme="dark") as layout, mock_app() as app:
        app.size.return_value = QSize(600, 400)
        overlay = create_aichat_overlay(app)
        overlay.body._chat_box.history_widget.add_message("user", "hello world")
        overlay.body._chat_box.history_widget.add_message("assistant", "Hi, 我是你的音乐助手")
        overlay.body._chat_box.history_widget.add_message("tools", "tools: play_model")
        overlay.show()
        layout.addWidget(overlay)
