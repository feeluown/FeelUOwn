import asyncio
import sys
from types import SimpleNamespace

from PyQt6.QtCore import QEvent, QPoint, QPointF, QRect, QSize, Qt, QTimer
from PyQt6.QtGui import QColor, QGuiApplication, QMouseEvent, QPalette
from PyQt6.QtWidgets import QListWidget, QWidget

from feeluown.ai import SongSuggestion
from feeluown.ai.copilot import CopilotArtifact
from feeluown.gui.helpers import secondary_text_color
from feeluown.library import BriefSongModel
from feeluown.media import Media
from feeluown.player import PlaybackMode, PlaylistMode, State
from feeluown.player.lyric import Line
from feeluown.utils.dispatch import Signal
from feeluown.gui.components.player_playlist import (
    PlayerPlaylistView,
    FMCandidatePlaylistDelegate,
)
from feeluown.gui.uimain.player_bar import PlayerControlPanel
from feeluown.gui.uimain.ai_chat import (
    AIChatOverlay,
    SongSuggestionItemWidget,
    song_suggestion_to_markdown_url,
    create_aichat_overlay,
    parse_song_link,
    parse_song_link_info,
)
from feeluown.gui.components.dynamic_island import (
    COMPACT_MIN_WIDTH,
    CONTENT_SPACING,
    COVER_COMPACT,
    COVER_EXPANDED,
    ISLAND_HEIGHT,
    PADDING_LEFT,
    PADDING_RIGHT,
    SEEK_STEP,
    DynamicIslandStatusBar,
    EXPANDED_WIDTH,
    VOLUME_STEP,
)
from feeluown.gui.uimain.mini_mode import MiniModeManager, MiniModeWindow
from feeluown.gui.uimain.lyric import LyricWindow
from feeluown.gui.uimain.playlist_overlay import PlaylistOverlay
from feeluown.gui.widgets.ai_chat import (
    ChatArtifactCard,
    ChatHistoryWidget,
    ChatMessageRow,
    ChatSendButton,
    ChatStreamingStatusCard,
    ChatToolEventCard,
    RoundedLabel,
    surface_border_color,
)
from feeluown.gui.widgets import PlayButton, PlusButton
from feeluown.gui.widgets.song_minicard_list import SongMiniCardListDelegate
from feeluown.gui.widgets.textbtn import TextButton


class FakeDelegateView(QWidget):
    def __init__(self):
        super().__init__()
        self.row_height = 0
        self.resize(320, 200)

    def set_row_height(self, height):
        self.row_height = height


class FakeIndex:
    def __init__(self, row):
        self._row = row

    def isValid(self):
        return True

    def row(self):
        return self._row

    def data(self, role):
        assert role == Qt.ItemDataRole.UserRole
        return (None, None)


class FakeActionSignal:
    def connect(self, _callback):
        pass


class FakeAction:
    def __init__(self, text=""):
        self.text = text
        self.triggered = FakeActionSignal()
        self._object_name = ""

    def setObjectName(self, name):
        self._object_name = name

    def objectName(self):
        return self._object_name


class FakeMenu:
    def __init__(self, _parent=None):
        self._actions = []

    def addAction(self, text):
        action = FakeAction(text)
        self._actions.append(action)
        return action

    def addSeparator(self):
        self._actions.append(FakeAction())

    def actions(self):
        return list(self._actions)

    def exec(self, _pos):
        pass


class FakeCopilot:
    def __init__(self):
        self.working_state_changed = Signal()
        self.artifact_added = Signal()
        self._artifacts = []

    def new_thread(self):
        self._artifacts = []

    def add_songs_artifact(self, songs, title=""):
        artifact = CopilotArtifact(
            identifier=len(self._artifacts) + 1,
            type="songs",
            title=title or "Songs",
            songs=songs,
        )
        self._artifacts.append(artifact)
        self.artifact_added.emit(artifact)
        return artifact

    def get_artifacts(self):
        return list(self._artifacts)

    async def match_song_suggestion(self, suggestion):
        return BriefSongModel(
            source="fake",
            identifier="matched",
            title=suggestion.title,
            artists_name=suggestion.artists_name,
        )


class FakeAI:
    def __init__(self, copilot=None):
        self._copilot = copilot or FakeCopilot()
        self.radio = None
        self.activate_radio_calls = []
        self.deactivate_radio_calls = 0

    def get_copilot(self):
        return self._copilot

    def get_active_radio(self):
        if self.radio is not None and self.radio.is_active:
            return self.radio
        return None

    def activate_radio(self, reset=True):
        self.activate_radio_calls.append(reset)
        radio = self.get_active_radio()
        if radio is not None:
            return radio
        self.radio = FakeAIRadio()
        return self.radio

    def deactivate_radio(self):
        self.deactivate_radio_calls += 1
        if self.radio is None:
            return False
        was_active = self.radio.is_active
        self.radio = None
        return was_active


class FakeAIRadio:
    is_active = True

    def __init__(self):
        self.status = "Updating candidates"
        self.status_changed = Signal()


class FakeThemeManager:
    def __init__(self):
        self.theme_changed = Signal()


class FakeStreamingCopilot(FakeCopilot):
    async def astream_user_query(self, _query):
        yield SimpleNamespace(
            content_blocks=[{"type": "text", "text": "我来"}]
        ), {"langgraph_node": "model"}
        self.add_songs_artifact(
            [
                SongSuggestion(
                    title="hello world",
                    artists_name="mary",
                    description="",
                )
            ],
            title="Night Songs",
        )
        yield SimpleNamespace(name="create_song_suggestions_artifact"), {
            "langgraph_node": "tools"
        }
        yield SimpleNamespace(
            content_blocks=[{"type": "text", "text": "我为您推荐了这些歌曲"}]
        ), {"langgraph_node": "model"}


class FakeAIRadioToolCopilot(FakeCopilot):
    async def astream_user_query(self, _query):
        yield SimpleNamespace(name="fm_candidates_remove"), {
            "langgraph_node": "tools"
        }
        yield SimpleNamespace(
            content_blocks=[{"type": "text", "text": "已更新候选歌曲"}]
        ), {"langgraph_node": "model"}


class FakeAIRadioLifecycleToolCopilot(FakeCopilot):
    async def astream_user_query(self, _query):
        yield SimpleNamespace(name="ai_radio_activate"), {
            "langgraph_node": "tools"
        }
        yield SimpleNamespace(
            content_blocks=[{"type": "text", "text": "AI 电台已开启"}]
        ), {"langgraph_node": "model"}


class PausedStreamingCopilot(FakeCopilot):
    def __init__(self):
        super().__init__()
        self.first_token_seen = asyncio.Event()
        self.resume = asyncio.Event()

    async def astream_user_query(self, _query):
        yield SimpleNamespace(
            content_blocks=[{"type": "text", "text": "我来"}]
        ), {"langgraph_node": "model"}
        self.first_token_seen.set()
        await self.resume.wait()
        yield SimpleNamespace(
            content_blocks=[{"type": "text", "text": "我为您推荐了这些歌曲"}]
        ), {"langgraph_node": "model"}


def _palette_with_colors(window, base, text="#111111", highlight="#3366cc"):
    pal = QPalette(QGuiApplication.palette())
    pal.setColor(QPalette.ColorRole.Window, QColor(window))
    pal.setColor(QPalette.ColorRole.Base, QColor(base))
    pal.setColor(QPalette.ColorRole.Text, QColor(text))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(text))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(text))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(base))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(highlight))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    return pal


def test_show_bitrate(qtbot, app_mock):
    app_mock.player.current_media = Media('http://', bitrate=100)
    w = PlayerControlPanel(app_mock)
    qtbot.addWidget(w)
    metadata = {'title': 'xx'}
    w.song_source_label.on_metadata_changed(metadata)
    assert '100kbps' in w.song_source_label.text()


def test_playlist_overlay(qtbot, app_mock):
    app_mock.playlist.playback_mode = PlaybackMode.one_loop
    app_mock.playlist.list.return_value = []
    app_mock.ai = None
    w = PlaylistOverlay(app_mock)
    qtbot.addWidget(w)
    w.show()
    # assert no error.
    w.show_tab(0)
    assert not w._ai_radio_btn.isEnabled()


def test_playlist_overlay_enter_ai_radio(qtbot, app_mock, mocker):
    app_mock.playlist.playback_mode = PlaybackMode.one_loop
    app_mock.playlist.mode = PlaylistMode.normal
    app_mock.ai = FakeAI()
    app_mock.fm.is_active = False
    app_mock.ui.ai_chat_overlay.show = mocker.MagicMock()
    app_mock.ui.ai_chat_overlay.raise_ = mocker.MagicMock()
    w = PlaylistOverlay(app_mock)
    qtbot.addWidget(w)

    w.enter_ai_radio()

    assert app_mock.ai.radio is not None
    assert app_mock.ai.activate_radio_calls == [True]
    app_mock.ui.ai_chat_overlay.show.assert_called_once()


def test_ai_chat_overlay_is_app_fullscreen(qtbot, app_mock):
    app_mock.ai = FakeAI()
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)

    overlay.show()
    qtbot.waitUntil(lambda: overlay.size() == parent.size())

    assert overlay.size() == parent.size()
    assert overlay.layout().contentsMargins().left() == 0
    assert overlay.layout().contentsMargins().top() == 0
    assert overlay.layout().contentsMargins().right() == 0
    assert overlay.layout().contentsMargins().bottom() == 0
    assert overlay.body._header.text() == "AI Assistant"
    island = overlay.body._chat_box._dynamic_island
    assert island.parent() is overlay.body._chat_box.input_widget
    assert overlay.body._toolbar_layout.indexOf(island) == -1
    assert not island.isVisible()
    assert not overlay.body._sidebar_panel.isVisible()
    assert isinstance(overlay.body._new_thread_btn, TextButton)
    assert isinstance(overlay.body._sidebar_btn, TextButton)
    assert isinstance(overlay.body._collapse_btn, TextButton)

    overlay.body._collapse_overlay()
    assert not overlay.isVisible()


def test_ai_chat_keeps_assistant_header_when_ai_radio_is_active(qtbot, app_mock):
    app_mock.ai = FakeAI()
    app_mock.ai.radio = FakeAIRadio()
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)

    overlay.show()

    assert overlay.body._header.text() == "AI Assistant"
    assert overlay.body._chat_box._dynamic_island.isHidden()
    assert overlay.body._new_thread_btn.isVisibleTo(overlay.body)
    assert overlay.body._sidebar_btn.isVisibleTo(overlay.body)
    assert overlay.body._collapse_btn.isVisibleTo(overlay.body)


def test_ai_chat_sidebar_button_toggles_inline_playlist(qtbot, app_mock, mocker):
    app_mock.ai = FakeAI()
    app_mock.ai.radio = FakeAIRadio()
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)

    overlay.show()
    assert not overlay.body._sidebar_panel.isVisible()
    assert isinstance(
        overlay.body._playlist_sidebar.itemDelegate(),
        FMCandidatePlaylistDelegate,
    )
    overlay.body._playlist_sidebar.scroll_to_current_song = mocker.MagicMock()

    overlay.body._sidebar_btn.click()
    assert overlay.body._sidebar_panel.isVisible()
    assert overlay.body._sidebar_shadow.isVisible()
    assert overlay.body._right_sidebar_stack.currentWidget() is (
        overlay.body._playlist_sidebar
    )
    assert overlay.isVisible()
    overlay.body._playlist_sidebar.scroll_to_current_song.assert_called_once()

    overlay.body._sidebar_btn.click()
    assert not overlay.body._sidebar_panel.isVisible()
    assert not overlay.body._sidebar_shadow.isVisible()


def test_ai_chat_radio_query_updates_playlist_sidebar(qtbot, app_mock, mocker):
    app_mock.ai = FakeAI(FakeAIRadioToolCopilot())
    app_mock.ai.radio = FakeAIRadio()
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)
    overlay.body._playlist_sidebar.scroll_to_current_song = mocker.MagicMock()

    asyncio.run(overlay.body._chat_box.exec_user_query("换一批"))

    assert overlay.body._sidebar_panel.isVisibleTo(overlay.body)
    assert overlay.body._right_sidebar_stack.currentWidget() is (
        overlay.body._playlist_sidebar
    )
    assert overlay.body._sidebar_status_label.text() == "Updating candidates"
    assert overlay.body._sidebar_status_label.isVisibleTo(overlay.body)
    overlay.body._playlist_sidebar.scroll_to_current_song.assert_called()
    history_text = "\n".join(
        label.toPlainText()
        for label in overlay.body._chat_box.history_widget.findChildren(RoundedLabel)
    )
    assert "已更新候选歌曲" in history_text
    tool_events = overlay.body._chat_box.history_widget.findChildren(
        ChatToolEventCard
    )
    assert len(tool_events) == 1
    assert "fm_candidates_remove" in tool_events[0].text()


def test_ai_chat_radio_lifecycle_tool_opens_sidebar(qtbot, app_mock, mocker):
    app_mock.ai = FakeAI(FakeAIRadioLifecycleToolCopilot())
    app_mock.ai.radio = FakeAIRadio()
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)
    overlay.body._playlist_sidebar.scroll_to_current_song = mocker.MagicMock()

    asyncio.run(overlay.body._chat_box.exec_user_query("开启 AI 电台"))

    assert overlay.body._sidebar_panel.isVisibleTo(overlay.body)
    assert overlay.body._right_sidebar_stack.currentWidget() is (
        overlay.body._playlist_sidebar
    )
    overlay.body._playlist_sidebar.scroll_to_current_song.assert_called()
    history_text = "\n".join(
        label.toPlainText()
        for label in overlay.body._chat_box.history_widget.findChildren(RoundedLabel)
    )
    assert "AI 电台已开启" in history_text
    tool_events = overlay.body._chat_box.history_widget.findChildren(
        ChatToolEventCard
    )
    assert len(tool_events) == 1
    assert "ai_radio_activate" in tool_events[0].text()


def test_ai_chat_body_and_sidebar_use_distinct_background_roles(qtbot, app_mock):
    app_mock.ai = FakeAI()
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)
    qtbot.waitUntil(
        lambda: overlay.body._artifact_sidebar._song_list_view.palette().color(
            overlay.body._artifact_sidebar._song_list_view.palette().ColorRole.Window
        )
        == overlay.body.palette().color(overlay.body.palette().ColorRole.Base)
    )

    body_pal = overlay.body.palette()
    panel_pal = overlay.body._sidebar_panel.palette()
    sidebar_pal = overlay.body._right_sidebar_stack.palette()
    artifact_view = overlay.body._artifact_sidebar._song_list_view
    artifact_pal = artifact_view.palette()
    artifact_viewport_pal = artifact_view.viewport().palette()

    assert body_pal.color(body_pal.ColorRole.Window) == body_pal.color(
        body_pal.ColorRole.Base
    )
    assert sidebar_pal.color(sidebar_pal.ColorRole.Window) == sidebar_pal.color(
        sidebar_pal.ColorRole.Base
    )
    assert body_pal.color(body_pal.ColorRole.Window) != sidebar_pal.color(
        sidebar_pal.ColorRole.Window
    )
    assert panel_pal.color(panel_pal.ColorRole.Window) == sidebar_pal.color(
        sidebar_pal.ColorRole.Window
    )
    assert not overlay.body._sidebar_panel.autoFillBackground()
    assert not overlay.body._right_sidebar_stack.autoFillBackground()
    assert not overlay.body._playlist_sidebar.autoFillBackground()
    assert not overlay.body._playlist_sidebar.viewport().autoFillBackground()
    assert artifact_pal.color(artifact_pal.ColorRole.Window) == body_pal.color(
        body_pal.ColorRole.Base
    )
    assert artifact_viewport_pal.color(
        artifact_viewport_pal.ColorRole.Window
    ) == body_pal.color(body_pal.ColorRole.Base)
    assert not artifact_view.autoFillBackground()
    assert not artifact_view.viewport().autoFillBackground()
    history = overlay.body._chat_box.history_widget
    history_pal = history._history_area.palette()
    viewport_pal = history._history_area.viewport().palette()
    content_pal = history.history_widget.palette()
    assert history_pal.color(history_pal.ColorRole.Window) == body_pal.color(
        body_pal.ColorRole.Base
    )
    assert viewport_pal.color(viewport_pal.ColorRole.Window) == body_pal.color(
        body_pal.ColorRole.Base
    )
    assert content_pal.color(content_pal.ColorRole.Window) == body_pal.color(
        body_pal.ColorRole.Base
    )
    input_pal = overlay.body._chat_box.input_widget.palette()
    assert input_pal.color(input_pal.ColorRole.Window) != body_pal.color(
        body_pal.ColorRole.Window
    )
    editor = overlay.body._chat_box.input_widget._editor
    editor_pal = editor.palette()
    editor_viewport_pal = editor.viewport().palette()
    assert editor_pal.color(editor_pal.ColorRole.Window) == editor_pal.color(
        editor_pal.ColorRole.Base
    )
    assert editor_viewport_pal.color(
        editor_viewport_pal.ColorRole.Window
    ) == editor_pal.color(editor_pal.ColorRole.Window)
    assert editor.styleSheet()
    assert not editor.autoFillBackground()
    assert not editor.viewport().autoFillBackground()
    send_btn = overlay.body._chat_box.input_widget._send_btn
    assert isinstance(send_btn, ChatSendButton)
    assert send_btn.text() == ""
    assert send_btn.parent() is overlay.body._chat_box.input_widget


def test_ai_chat_renders_assistant_markdown(qtbot):
    history = ChatHistoryWidget()
    qtbot.addWidget(history)

    label = history.create_message_label("assistant", "**Bold**\n\n- item")

    assert 'name="qrichtext"' in label.text()
    assert "font-weight:700" in label.text()
    assert "Bold" in label.text()
    assert ">item</li>" in label.text()


def test_ai_chat_user_message_has_limited_width(qtbot):
    history = ChatHistoryWidget()
    history.resize(900, 400)
    qtbot.addWidget(history)
    history.show()

    user_label = history.create_message_label(
        "user",
        "这是一段比较长的用户输入，显示在对话流里时不应该铺满整行。",
    )
    assistant_label = history.create_message_label("assistant", "assistant")
    qtbot.waitUntil(lambda: user_label.parent().width() > 400)

    user_row = user_label.parent()
    assert isinstance(user_row, ChatMessageRow)
    assert user_row.role == "user"
    assert user_label.maximumWidth() < user_row.width()
    assert user_label.maximumWidth() == max(240, int(user_row.width() * 0.7))
    assert assistant_label.maximumWidth() == 16777215


def test_ai_chat_message_background_roles(qtbot):
    original_palette = QGuiApplication.palette()
    test_palette = _palette_with_colors("#eeeeee", "#ffffff")
    QGuiApplication.setPalette(test_palette)
    try:
        history = ChatHistoryWidget()
        qtbot.addWidget(history)

        user_label = history.create_message_label("user", "hello")
        assistant_label = history.create_message_label("assistant", "hello")

        user_pal = user_label.palette()
        assistant_pal = assistant_label.palette()
        assert user_label.backgroundRole() == user_pal.ColorRole.Window
        assert assistant_label.backgroundRole() == assistant_pal.ColorRole.Base
        assert user_label._surface_visible
        assert not assistant_label._surface_visible
        assert user_pal.color(user_label.backgroundRole()) == test_palette.color(
            test_palette.ColorRole.Window
        )
        assert assistant_pal.color(
            assistant_label.backgroundRole()
        ) == test_palette.color(test_palette.ColorRole.Base)
        assert user_pal.color(user_label.backgroundRole()) != assistant_pal.color(
            assistant_label.backgroundRole()
        )
    finally:
        QGuiApplication.setPalette(original_palette)


def test_ai_chat_tool_event_aligns_with_assistant_text(qtbot):
    history = ChatHistoryWidget()
    history.resize(900, 500)
    qtbot.addWidget(history)
    history.show()

    assistant_label = history.create_message_label("assistant", "assistant")
    tool_card = history.add_tool_event("Tool called: ai_radio_get_state")
    qtbot.waitUntil(lambda: tool_card._label.x() > 0)

    assert tool_card._label.mapTo(history.history_widget, QPoint(0, 0)).x() == (
        assistant_label.viewport().mapTo(history.history_widget, QPoint(0, 0)).x()
        + int(assistant_label.document().documentMargin())
    )


def test_ai_chat_refreshes_palette_roles(qtbot, app_mock):
    original_palette = QGuiApplication.palette()
    light_palette = _palette_with_colors("#f0f0f0", "#ffffff")
    dark_palette = _palette_with_colors(
        "#303030", "#202020", text="#eeeeee", highlight="#6d8dff"
    )
    QGuiApplication.setPalette(light_palette)
    try:
        app_mock.ai = FakeAI()
        app_mock.ai.radio = FakeAIRadio()
        app_mock.playlist.list.return_value = []
        app_mock.theme_mgr = FakeThemeManager()
        parent = QWidget()
        parent.resize(QSize(960, 600))
        parent.show()
        qtbot.addWidget(parent)
        app_mock.size.return_value = parent.size()
        overlay = create_aichat_overlay(app_mock, parent=parent)
        history = overlay.body._chat_box.history_widget
        user_label = history.create_message_label("user", "hello")
        assistant_label = history.create_message_label("assistant", "hello")
        status_card = history.add_streaming_status("thinking")
        tool_card = history.add_tool_event(
            "Tool called: create_song_suggestions_artifact"
        )
        overlay.body._chat_box.input_widget.set_msg("AI Radio is active")

        QGuiApplication.setPalette(dark_palette)
        app_mock.theme_mgr.theme_changed.emit("dark")
        qtbot.waitUntil(
            lambda: overlay.body._sidebar_panel.palette().color(
                overlay.body._sidebar_panel.palette().ColorRole.Window
            ) == dark_palette.color(dark_palette.ColorRole.Window)
        )

        body_pal = overlay.body.palette()
        sidebar_pal = overlay.body._sidebar_panel.palette()
        input_widget = overlay.body._chat_box.input_widget
        assert body_pal.color(body_pal.ColorRole.Window) == dark_palette.color(
            dark_palette.ColorRole.Base
        )
        assert sidebar_pal.color(sidebar_pal.ColorRole.Window) == dark_palette.color(
            dark_palette.ColorRole.Window
        )
        assert user_label.palette().color(
            user_label.backgroundRole()
        ) == dark_palette.color(dark_palette.ColorRole.Window)
        assert assistant_label.palette().color(
            assistant_label.backgroundRole()
        ) == dark_palette.color(dark_palette.ColorRole.Base)
        assert history._history_area.palette().color(
            history._history_area.palette().ColorRole.Window
        ) == dark_palette.color(dark_palette.ColorRole.Base)
        assert input_widget.palette().color(
            input_widget.palette().ColorRole.Window
        ) == dark_palette.color(dark_palette.ColorRole.Window)
        assert not overlay.body._playlist_sidebar.autoFillBackground()
        assert not overlay.body._playlist_sidebar.viewport().autoFillBackground()
        assert input_widget._msg_label.textFormat() == Qt.TextFormat.PlainText
        assert input_widget._msg_label.text() == "AI Radio is active"
        assert input_widget._msg_label.isHidden()
        assert "color:" not in input_widget._msg_label.text()
        assert input_widget._msg_label.palette().color(
            input_widget._msg_label.palette().ColorRole.WindowText
        ) == secondary_text_color(dark_palette)
        assert status_card._label.palette().color(
            status_card._label.palette().ColorRole.WindowText
        ) == dark_palette.color(dark_palette.ColorRole.WindowText)
        assert status_card.palette().color(
            status_card.palette().ColorRole.Window
        ) == dark_palette.color(dark_palette.ColorRole.Window)
        assert tool_card._label.palette().color(
            tool_card._label.palette().ColorRole.WindowText
        ) == secondary_text_color(dark_palette)
        island = overlay.body._chat_box._dynamic_island
        assert island.parent() is input_widget
        island_pal = island.palette()
        assert island_pal.color(
            island_pal.ColorRole.WindowText
        ) == dark_palette.color(dark_palette.ColorRole.WindowText)
        border_color = surface_border_color(dark_palette, QPalette.ColorRole.Base)
        assert border_color.alpha() > 0
        assert border_color != dark_palette.color(dark_palette.ColorRole.Mid)
    finally:
        QGuiApplication.setPalette(original_palette)


def test_ai_chat_theme_change_refreshes_after_delayed_palette(qtbot, app_mock):
    original_palette = QGuiApplication.palette()
    light_palette = _palette_with_colors("#f0f0f0", "#ffffff")
    dark_palette = _palette_with_colors(
        "#303030", "#202020", text="#eeeeee", highlight="#6d8dff"
    )
    QGuiApplication.setPalette(light_palette)
    try:
        app_mock.ai = FakeAI()
        app_mock.ai.radio = None
        app_mock.playlist.list.return_value = []
        app_mock.theme_mgr = FakeThemeManager()
        parent = QWidget()
        parent.resize(QSize(960, 600))
        parent.show()
        qtbot.addWidget(parent)
        app_mock.size.return_value = parent.size()
        overlay = create_aichat_overlay(app_mock, parent=parent)

        QTimer.singleShot(10, lambda: QGuiApplication.setPalette(dark_palette))
        QTimer.singleShot(20, lambda: app_mock.theme_mgr.theme_changed.emit("dark"))

        qtbot.waitUntil(
            lambda: overlay.body.palette().color(
                overlay.body.palette().ColorRole.Window
            ) == dark_palette.color(dark_palette.ColorRole.Base)
        )

        history_area = overlay.body._chat_box.history_widget._history_area
        assert history_area.palette().color(
            history_area.palette().ColorRole.Window
        ) == dark_palette.color(dark_palette.ColorRole.Base)
        assert overlay.body._chat_box.input_widget.palette().color(
            overlay.body._chat_box.input_widget.palette().ColorRole.Window
        ) == dark_palette.color(dark_palette.ColorRole.Window)
    finally:
        QGuiApplication.setPalette(original_palette)


def test_ai_chat_theme_change_reapplies_self_painted_palettes(qtbot, app_mock):
    original_palette = QGuiApplication.palette()
    light_palette = _palette_with_colors("#f0f0f0", "#ffffff")
    dirty_palette = _palette_with_colors("#111111", "#121212")
    QGuiApplication.setPalette(light_palette)
    try:
        app_mock.ai = FakeAI()
        app_mock.ai.radio = None
        app_mock.playlist.list.return_value = []
        app_mock.theme_mgr = FakeThemeManager()
        parent = QWidget()
        parent.resize(QSize(960, 600))
        parent.show()
        qtbot.addWidget(parent)
        app_mock.size.return_value = parent.size()
        overlay = create_aichat_overlay(app_mock, parent=parent)

        overlay.body._sidebar_panel.setPalette(dirty_palette)
        overlay.body._chat_box.input_widget.setPalette(dirty_palette)
        app_mock.theme_mgr.theme_changed.emit("light")

        sidebar_pal = overlay.body._sidebar_panel.palette()
        input_pal = overlay.body._chat_box.input_widget.palette()
        assert sidebar_pal.color(sidebar_pal.ColorRole.Window) == light_palette.color(
            light_palette.ColorRole.Window
        )
        assert input_pal.color(input_pal.ColorRole.Window) == light_palette.color(
            light_palette.ColorRole.Window
        )
    finally:
        QGuiApplication.setPalette(original_palette)


def _prepare_dynamic_island_app(app_mock):
    app_mock.player.metadata_changed = Signal()
    app_mock.player.state_changed = Signal()
    app_mock.player.volume_changed = Signal()
    app_mock.player.position_changed = Signal()
    app_mock.player.duration_changed = Signal()
    app_mock.player.state = State.playing
    app_mock.player.current_metadata = {}
    app_mock.player.position = 20
    app_mock.player.duration = 100
    app_mock.player.volume = 50
    app_mock.live_lyric.line_changed = Signal()
    app_mock.live_lyric.current_line = Line("", "", False)
    app_mock.playlist.play_model_stage_changed = Signal()
    return app_mock


def test_dynamic_island_keeps_height_when_expanded(qtbot, app_mock):
    _prepare_dynamic_island_app(app_mock)
    island = DynamicIslandStatusBar(app_mock)
    qtbot.addWidget(island)

    island._on_metadata_changed(
        {
            "title": "Hi",
            "artists": ["Mary"],
            "artwork": "",
            "source": "fake",
        }
    )
    compact_height = island.height()
    compact_width = island.width()

    island._start_expand()
    while island._animating:
        island._tick_animation()

    assert compact_height == ISLAND_HEIGHT
    assert island.height() == compact_height
    assert island.width() == EXPANDED_WIDTH
    assert compact_width >= COMPACT_MIN_WIDTH
    assert island._cover.width() == COVER_EXPANDED
    assert island._cover.height() == COVER_EXPANDED


def test_dynamic_island_syncs_current_cover_and_lyric_on_init(
    qtbot, app_mock, monkeypatch
):
    _prepare_dynamic_island_app(app_mock)
    app_mock.player.current_metadata = {
        "title": "Song",
        "artists": ["Mary"],
        "artwork": "http://example.test/cover.jpg",
        "source": "fake",
        "uri": "fuo://fake/songs/1",
    }
    app_mock.live_lyric.current_line = Line("Current lyric", "", False)
    calls = []
    monkeypatch.setattr(
        "feeluown.gui.components.dynamic_island.run_afn",
        lambda *args: calls.append(args),
    )

    island = DynamicIslandStatusBar(app_mock)
    qtbot.addWidget(island)

    assert calls == [
        (
            island._cover.show_cover_with_source,
            "http://example.test/cover.jpg",
            "fake",
            "fuo://fake/songs/1",
        )
    ]
    assert island._lyric_label.text() == "Current lyric"
    assert island._cover.width() == COVER_COMPACT
    assert island._cover.height() == COVER_COMPACT


def test_dynamic_island_metadata_does_not_replace_compact_lyric(qtbot, app_mock):
    _prepare_dynamic_island_app(app_mock)
    island = DynamicIslandStatusBar(app_mock)
    qtbot.addWidget(island)

    island._on_lyric_line_changed(Line("Stay as lyric", "", False))
    island._on_metadata_changed(
        {
            "title": "Song title",
            "artists": ["Mary"],
            "artwork": "",
            "source": "fake",
        }
    )

    assert island._lyric_label.toolTip() == "Stay as lyric"
    assert island._lyric_label.alignment() == Qt.AlignmentFlag.AlignCenter


def test_dynamic_island_compact_lyric_has_width_padding(qtbot, app_mock):
    _prepare_dynamic_island_app(app_mock)
    island = DynamicIslandStatusBar(app_mock)
    qtbot.addWidget(island)

    island._on_lyric_line_changed(Line("abc", "", False))

    assert island._lyric_label.width() > (
        island._lyric_label.fontMetrics().horizontalAdvance("abc")
    )
    assert island._lyric_label.text() == "abc"


def test_dynamic_island_compact_right_padding_matches_cover_left(qtbot, app_mock):
    _prepare_dynamic_island_app(app_mock)
    island = DynamicIslandStatusBar(app_mock)
    qtbot.addWidget(island)

    island._on_lyric_line_changed(Line("padding check lyric", "", False))

    assert PADDING_RIGHT == PADDING_LEFT
    assert island.width() == (
        PADDING_LEFT + COVER_COMPACT + CONTENT_SPACING +
        island._lyric_label.width() + PADDING_RIGHT
    )


def test_dynamic_island_compact_width_tracks_lyric(qtbot, app_mock):
    _prepare_dynamic_island_app(app_mock)
    island = DynamicIslandStatusBar(app_mock)
    qtbot.addWidget(island)

    island._on_lyric_line_changed(Line("short", "", False))
    short_width = island.width()
    island._on_lyric_line_changed(
        Line(
            (
                "This is a fairly long lyric line that should be elided "
                "inside the island"
            ),
            "",
            False,
        )
    )

    assert short_width >= COMPACT_MIN_WIDTH
    assert short_width < island.width()
    assert island.width() == EXPANDED_WIDTH
    assert island._lyric_label.width() == island._compact_text_max_width()
    assert island._lyric_label.alignment() == Qt.AlignmentFlag.AlignCenter


def test_dynamic_island_restores_current_lyric_after_hover(qtbot, app_mock):
    _prepare_dynamic_island_app(app_mock)
    app_mock.player.current_metadata = {
        "title": "Song",
        "artists": ["Mary"],
        "artwork": "",
        "source": "fake",
    }
    app_mock.live_lyric.current_line = Line("Lyric while expanded", "", False)
    island = DynamicIslandStatusBar(app_mock)
    qtbot.addWidget(island)

    island._start_expand()
    while island._animating:
        island._tick_animation()
    assert island._song_label.isVisible()

    island._switch_to_compact()

    assert island._lyric_label.toolTip() == "Lyric while expanded"
    assert island._lyric_label.text().startswith("Lyric while")


def test_dynamic_island_keyboard_controls_player(qtbot, app_mock):
    _prepare_dynamic_island_app(app_mock)
    island = DynamicIslandStatusBar(app_mock)
    qtbot.addWidget(island)

    island.keyPressEvent(
        SimpleNamespace(key=lambda: Qt.Key.Key_Right, accept=lambda: None)
    )
    assert app_mock.player.position == 20 + SEEK_STEP
    island.keyPressEvent(
        SimpleNamespace(key=lambda: Qt.Key.Key_Left, accept=lambda: None)
    )
    assert app_mock.player.position == 20
    island.keyPressEvent(
        SimpleNamespace(key=lambda: Qt.Key.Key_Up, accept=lambda: None)
    )
    assert app_mock.player.volume == 50 + VOLUME_STEP
    island.keyPressEvent(
        SimpleNamespace(key=lambda: Qt.Key.Key_Down, accept=lambda: None)
    )
    assert app_mock.player.volume == 50


def test_dynamic_island_expanded_controls_include_volume(qtbot, app_mock):
    _prepare_dynamic_island_app(app_mock)
    island = DynamicIslandStatusBar(app_mock)
    qtbot.addWidget(island)

    assert island.focusPolicy() == Qt.FocusPolicy.StrongFocus
    island._switch_to_expanded()
    island._volume_btn.setValue(72)

    assert not island._volume_btn.isHidden()
    assert island._control_widget.layout().indexOf(island._volume_btn) >= 0
    assert app_mock.player.volume == 72


def test_dynamic_island_progress_updates_only_when_expanded(qtbot, app_mock, mocker):
    _prepare_dynamic_island_app(app_mock)
    island = DynamicIslandStatusBar(app_mock)
    qtbot.addWidget(island)
    update = mocker.patch.object(island, "update")

    assert island._playback_progress() == 0.2
    island._on_position_changed(50)
    update.assert_not_called()

    island._switch_to_expanded()
    update.reset_mock()
    island._on_duration_changed(200)

    assert island._playback_progress() == 0.25
    update.assert_called_once()


class _FakeMouseEvent:
    def __init__(
        self,
        event_type,
        global_pos,
        button=Qt.MouseButton.LeftButton,
        local_pos=None,
    ):
        self._event_type = event_type
        self._global_pos = QPointF(global_pos)
        self._local_pos = QPointF(local_pos if local_pos is not None else global_pos)
        self._button = button
        self.accepted = False

    def type(self):
        return self._event_type

    def button(self):
        return self._button

    def globalPosition(self):
        return self._global_pos

    def position(self):
        return self._local_pos

    def accept(self):
        self.accepted = True


class _FakeContextMenuEvent:
    def __init__(self, global_pos):
        self._global_pos = QPoint(global_pos)

    def type(self):
        return QEvent.Type.ContextMenu

    def globalPos(self):
        return self._global_pos


def test_mini_mode_window_is_frameless_and_uses_island(qtbot, app_mock):
    _prepare_dynamic_island_app(app_mock)
    window = MiniModeWindow(app_mock)
    qtbot.addWidget(window)
    margins = window.layout().contentsMargins()

    assert isinstance(window.island, DynamicIslandStatusBar)
    assert window.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    assert window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert margins.left() == 0
    assert margins.top() == 0
    assert margins.right() == 0
    assert margins.bottom() == 0


def test_mini_mode_window_drags_from_island_body(qtbot, app_mock, monkeypatch):
    _prepare_dynamic_island_app(app_mock)
    window = MiniModeWindow(app_mock)
    qtbot.addWidget(window)
    window.move(100, 120)
    monkeypatch.setattr(window, "_start_system_move", lambda: False)

    window._handle_drag_event(
        window.island,
        _FakeMouseEvent(QEvent.Type.MouseButtonPress, QPointF(10, 10)),
    )
    window._handle_drag_event(
        window.island,
        _FakeMouseEvent(QEvent.Type.MouseMove, QPointF(25, 28)),
    )
    window._handle_drag_event(
        window.island,
        _FakeMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(25, 28)),
    )

    assert window.pos() == QPoint(115, 138)
    assert window._drag_global_pos is None


def test_mini_mode_window_prefers_system_move(qtbot, app_mock, monkeypatch):
    _prepare_dynamic_island_app(app_mock)
    window = MiniModeWindow(app_mock)
    qtbot.addWidget(window)
    window.move(100, 120)
    monkeypatch.setattr(window, "_start_system_move", lambda: True)

    handled = window._handle_drag_event(
        window.island,
        _FakeMouseEvent(QEvent.Type.MouseButtonPress, QPointF(10, 10)),
    )
    moved = window._handle_drag_event(
        window.island,
        _FakeMouseEvent(QEvent.Type.MouseMove, QPointF(25, 28)),
    )
    released = window._handle_drag_event(
        window.island,
        _FakeMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(25, 28)),
    )

    assert handled
    assert moved
    assert released
    assert window.pos() == QPoint(100, 120)
    assert window._drag_global_pos is None
    assert not window._using_system_move


def test_mini_mode_window_does_not_drag_from_controls(qtbot, app_mock):
    _prepare_dynamic_island_app(app_mock)
    window = MiniModeWindow(app_mock)
    qtbot.addWidget(window)
    window.move(100, 120)

    window._handle_drag_event(
        window.island._pp_btn,
        _FakeMouseEvent(QEvent.Type.MouseButtonPress, QPointF(10, 10)),
    )
    window._handle_drag_event(
        window.island._pp_btn,
        _FakeMouseEvent(QEvent.Type.MouseMove, QPointF(25, 28)),
    )

    assert window.pos() == QPoint(100, 120)


def test_mini_mode_window_intercepts_child_context_menu(
    qtbot, app_mock, monkeypatch
):
    _prepare_dynamic_island_app(app_mock)
    window = MiniModeWindow(app_mock)
    qtbot.addWidget(window)
    positions = []
    monkeypatch.setattr(window, "_show_context_menu", positions.append)

    handled = window.eventFilter(
        window.island._song_label,
        _FakeContextMenuEvent(QPoint(20, 30)),
    )

    assert handled
    assert positions == [QPoint(20, 30)]


def test_mini_mode_manager_hides_and_restores_main_window(qtbot, app_mock):
    _prepare_dynamic_island_app(app_mock)
    app_mock.isVisible.return_value = True
    app_mock.geometry.return_value = QRect(100, 120, 640, 480)
    manager = MiniModeManager(app_mock)
    qtbot.addWidget(manager.window)
    changes = []
    manager.mode_changed.connect(changes.append)

    manager.enter()

    assert manager.is_active
    assert manager.window.isVisible()
    app_mock.hide.assert_called_once()
    assert changes == [True]

    manager.exit()

    assert not manager.is_active
    assert not manager.window.isVisible()
    app_mock.show.assert_called_once()
    app_mock.activateWindow.assert_called_once()
    assert changes == [True, False]


def _prepare_lyric_window_app(app_mock):
    app_mock.live_lyric.line_changed = Signal()
    app_mock.live_lyric.lyrics_changed = Signal()
    app_mock.live_lyric.current_line = Line("", "", False)
    return app_mock


def test_lyric_window_drag_uses_system_move(qtbot, app_mock, monkeypatch):
    _prepare_lyric_window_app(app_mock)
    window = LyricWindow(app_mock)
    qtbot.addWidget(window)
    window.move(100, 120)
    monkeypatch.setattr(window, "_start_system_move", lambda: True)

    press = _FakeMouseEvent(QEvent.Type.MouseButtonPress, QPointF(10, 10))
    move = _FakeMouseEvent(QEvent.Type.MouseMove, QPointF(25, 28))
    release = _FakeMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(25, 28))

    window.mousePressEvent(press)
    window.mouseMoveEvent(move)
    window.mouseReleaseEvent(release)

    assert press.accepted
    assert move.accepted
    assert release.accepted
    assert window.pos() == QPoint(100, 120)
    assert window._old_pos is None
    assert not window._using_system_move


def test_lyric_window_drag_falls_back_to_manual_move(
    qtbot, app_mock, monkeypatch
):
    _prepare_lyric_window_app(app_mock)
    window = LyricWindow(app_mock)
    qtbot.addWidget(window)
    window.move(100, 120)
    monkeypatch.setattr(window, "_start_system_move", lambda: False)

    press = _FakeMouseEvent(QEvent.Type.MouseButtonPress, QPointF(10, 10))
    move = _FakeMouseEvent(QEvent.Type.MouseMove, QPointF(25, 28))
    release = _FakeMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(25, 28))

    window.mousePressEvent(press)
    window.mouseMoveEvent(move)
    window.mouseReleaseEvent(release)

    assert window.pos() == QPoint(115, 138)
    assert window._old_pos is None
    assert not window._using_system_move


def test_ai_chat_assistant_rows_keep_content_height(qtbot):
    history = ChatHistoryWidget()
    history.resize(900, 500)
    qtbot.addWidget(history)
    history.show()

    first_label = history.create_message_label("assistant", "第一段回复")
    second_label = history.create_message_label("assistant", "第二段回复")
    first_row = first_label.parent()
    second_row = second_label.parent()

    qtbot.waitUntil(lambda: second_row.y() > first_row.y())

    assert first_row.height() == first_row.sizeHint().height()
    assert second_row.y() - first_row.y() == (
        first_row.height() + history._history_layout.spacing()
    )


def test_ai_chat_emits_markdown_link_signal(qtbot):
    history = ChatHistoryWidget()
    qtbot.addWidget(history)
    urls = []
    history.link_activated.connect(urls.append)

    label = history.create_message_label(
        "assistant",
        "[Song](fuo://song-suggestion?title=hello&artists=mary)",
    )

    label.link_activated.emit("fuo://song-suggestion?title=hello&artists=mary")
    assert urls == ["fuo://song-suggestion?title=hello&artists=mary"]


def test_ai_chat_history_renders_artifact_card(qtbot):
    history = ChatHistoryWidget()
    qtbot.addWidget(history)
    artifact = CopilotArtifact(
        identifier=1,
        type="songs",
        title="Night Songs",
        songs=[
            SongSuggestion(
                title="hello world",
                artists_name="mary",
                description="",
            )
        ],
    )

    card = history.add_artifact(artifact)

    assert isinstance(card, ChatArtifactCard)
    assert card.artifact is artifact


def test_ai_chat_shows_song_artifact_in_right_sidebar(qtbot, app_mock):
    app_mock.ai = FakeAI()
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)
    artifact = CopilotArtifact(
        identifier=1,
        type="songs",
        title="Night Songs",
        songs=[
            SongSuggestion(
                title="hello world",
                artists_name="mary",
                description="",
            )
        ],
    )

    overlay.body.show_artifact(artifact)

    assert overlay.body._sidebar_panel.isVisibleTo(overlay.body)
    assert overlay.body._right_sidebar_stack.currentWidget() is (
        overlay.body._artifact_sidebar
    )
    view = overlay.body._artifact_sidebar._song_list_view
    assert isinstance(view, QListWidget)
    assert view._radius == 8
    model = view.model()
    assert model.rowCount() == 1
    item = view.item(0)
    item_widget = view.itemWidget(item)
    assert isinstance(item_widget, SongSuggestionItemWidget)
    assert isinstance(item_widget.play_btn, PlayButton)
    assert isinstance(item_widget.add_btn, PlusButton)
    display_song = item.data(Qt.ItemDataRole.UserRole)
    assert display_song.title == "hello world"
    assert display_song.artists_name == "mary"
    assert item_widget.song is display_song


def test_ai_chat_shows_search_result_artifact_song(qtbot, app_mock):
    app_mock.ai = FakeAI()
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)
    song = BriefSongModel(
        source="fake",
        identifier="song-1",
        title="Song",
        artists_name="Mary",
    )
    artifact = CopilotArtifact(
        identifier=1,
        type="search_result",
        title="Song",
        songs=[song],
        result=object(),
    )

    overlay.body.show_artifact(artifact)

    view = overlay.body._artifact_sidebar._song_list_view
    item = view.item(0)
    item_widget = view.itemWidget(item)
    display_song = item.data(Qt.ItemDataRole.UserRole)
    assert item_widget.song is song
    assert display_song is song
    assert view._suggestion_by_display_song == {}


def test_ai_chat_parses_song_links():
    suggestion = SongSuggestion(title="hello world", artists_name="mary", description="")

    parsed_suggestion_info = parse_song_link_info(
        song_suggestion_to_markdown_url(suggestion)
    )
    assert parsed_suggestion_info.kind == "suggestion"
    parsed_suggestion = parsed_suggestion_info.model
    assert isinstance(parsed_suggestion, SongSuggestion)
    assert parsed_suggestion.title == "hello world"
    assert parsed_suggestion.artists_name == "mary"
    parsed_legacy_suggestion_info = parse_song_link_info(
        "fuo://ai-song?title=hello&artists=mary"
    )
    assert parsed_legacy_suggestion_info.kind == "suggestion"
    parsed_legacy_suggestion = parsed_legacy_suggestion_info.model
    assert isinstance(parsed_legacy_suggestion, SongSuggestion)

    parsed_song_info = parse_song_link_info(
        "fuo://song?source=fake&identifier=1&title=hello&artists=mary"
    )
    assert parsed_song_info.kind == "resource"
    parsed_song = parsed_song_info.model
    assert isinstance(parsed_song, BriefSongModel)
    assert parsed_song.source == "fake"
    assert parsed_song.identifier == "1"

    parsed_provider_song_info = parse_song_link_info("fuo://fake/songs/1")
    assert parsed_provider_song_info.kind == "resource"
    parsed_provider_song = parsed_provider_song_info.model
    assert isinstance(parsed_provider_song, BriefSongModel)
    assert parsed_provider_song.source == "fake"
    assert parsed_provider_song.identifier == "1"

    assert parse_song_link(song_suggestion_to_markdown_url(suggestion)) == (
        parsed_suggestion
    )


def test_ai_chat_link_context_menu_differs_by_link_type(qtbot, app_mock, mocker):
    app_mock.ai = FakeAI()
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)
    menus = []

    class CapturingMenu(FakeMenu):
        def exec(self, _pos):
            menus.append([action.objectName() for action in self.actions()])

    mocker.patch("feeluown.gui.uimain.ai_chat.QMenu", CapturingMenu)

    overlay.body._on_link_context_menu_requested(
        "fuo://song-suggestion?title=hello&artists=mary",
        QPoint(0, 0),
    )
    overlay.body._on_link_context_menu_requested(
        "fuo://fake/songs/1",
        QPoint(0, 0),
    )

    assert "ai-chat-link-search" in menus[0]
    assert "ai-chat-link-play" in menus[0]
    assert "ai-chat-link-add-to-playlist" in menus[0]
    assert "ai-chat-link-copy" in menus[0]
    assert "ai-chat-link-search" not in menus[1]
    assert "ai-chat-link-play" in menus[1]
    assert "ai-chat-link-add-to-playlist" in menus[1]
    assert "ai-chat-link-copy" in menus[1]


def test_ai_chat_toolbar_starts_system_move(qtbot, app_mock, mocker):
    app_mock.ai = FakeAI()
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)
    window = mocker.Mock()
    window.startSystemMove.return_value = True
    overlay.body._toolbar._window_handle = mocker.Mock(return_value=window)

    overlay.show()
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(1, 1),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    overlay.body._toolbar.mousePressEvent(event)

    window.startSystemMove.assert_called_once()


def test_player_playlist_view_does_not_own_delegate(qtbot, app_mock):
    app_mock.playlist.list.return_value = []
    view = PlayerPlaylistView(app_mock)
    qtbot.addWidget(view)

    assert not isinstance(view.itemDelegate(), SongMiniCardListDelegate)


def test_fm_candidate_delegate_marks_only_upcoming_playlist_songs(
    qtbot,
    app_mock,
    song,
    song1,
    song2,
):
    PlayerPlaylistView._model = None
    app_mock.ai = FakeAI()
    app_mock.playlist.mode = PlaylistMode.fm
    app_mock.playlist.list.return_value = [song, song1, song2]
    app_mock.playlist.current_song = song
    app_mock.playlist.current_song_index.return_value = 0
    view = FakeDelegateView()
    qtbot.addWidget(view)
    delegate = FMCandidatePlaylistDelegate(app_mock, view)

    assert not delegate.is_fm_candidate(FakeIndex(0))
    assert delegate.is_fm_candidate(FakeIndex(1))
    assert delegate.is_fm_candidate(FakeIndex(2))

    app_mock.playlist.current_song_index.return_value = None
    assert delegate.is_fm_candidate(FakeIndex(0))

    app_mock.playlist.mode = PlaylistMode.normal
    assert not delegate.is_fm_candidate(FakeIndex(1))


def test_playlist_overlay_uses_fm_candidate_delegate_on_playlist_tab(
    qtbot,
    app_mock,
):
    PlayerPlaylistView._model = None
    app_mock.playlist.playback_mode = PlaybackMode.one_loop
    app_mock.playlist.mode = PlaylistMode.fm
    app_mock.playlist.list.return_value = []
    app_mock.ai = FakeAI()
    app_mock.ai.radio = FakeAIRadio()
    app_mock.fm.is_active = False
    app_mock.size.return_value = QSize(960, 600)
    w = PlaylistOverlay(app_mock)
    qtbot.addWidget(w)

    w.show()
    w.show_tab(0)

    assert isinstance(
        w._player_playlist_view.itemDelegate(),
        FMCandidatePlaylistDelegate,
    )


def test_ai_chat_overlay_toggles_titlebar_mode(qtbot, app_mock, mocker):
    titlebar_mode = SimpleNamespace(
        enter=mocker.MagicMock(),
        exit=mocker.MagicMock(),
        reapply=mocker.MagicMock(),
    )
    mocker.patch(
        "feeluown.gui.uimain.ai_chat._create_titlebar_mode",
        return_value=titlebar_mode,
    )
    app_mock.ai = FakeAI()
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)
    assert isinstance(overlay, AIChatOverlay)

    overlay.show()
    overlay.hide()

    titlebar_mode.enter.assert_called_once()
    titlebar_mode.exit.assert_called_once()


def test_ai_chat_overlay_reapplies_titlebar_mode_on_resize(qtbot, app_mock, mocker):
    titlebar_mode = SimpleNamespace(
        enter=mocker.MagicMock(),
        exit=mocker.MagicMock(),
        reapply=mocker.MagicMock(),
    )
    mocker.patch(
        "feeluown.gui.uimain.ai_chat._create_titlebar_mode",
        return_value=titlebar_mode,
    )
    app = QWidget()
    app.ai = FakeAI()
    app.ai.radio = None
    app.theme_mgr = FakeThemeManager()
    # Mock player for LineSongLabel and DynamicIslandStatusBar
    app.player = app_mock.player
    app.player.metadata_changed = Signal()
    app.player.state_changed = Signal()
    app.player.state = State.stopped
    app.live_lyric = app_mock.live_lyric
    app.live_lyric.line_changed = Signal()
    app.playlist = app_mock.playlist
    app.playlist.mode_changed = Signal()
    app.playlist.list.return_value = []
    app.resize(QSize(960, 600))
    app.show()
    qtbot.addWidget(app)
    overlay = create_aichat_overlay(app, parent=app)
    assert isinstance(overlay, AIChatOverlay)

    overlay.show()
    app.resize(QSize(1000, 640))
    qtbot.waitUntil(lambda: titlebar_mode.reapply.called)

    titlebar_mode.reapply.assert_called_once()


def test_ai_chat_overlay_skips_titlebar_mode_outside_macos(qtbot, app_mock, mocker):
    mocker.patch("feeluown.gui.uimain.ai_chat.IS_MACOS", False)
    sys.modules.pop("feeluown.gui.macos_titlebar", None)
    app_mock.ai = FakeAI()
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()

    overlay = create_aichat_overlay(app_mock, parent=parent)

    assert isinstance(overlay, AIChatOverlay)
    assert overlay._titlebar_mode is None
    assert "feeluown.gui.macos_titlebar" not in sys.modules


def test_ai_chat_copilot_artifact_signal_renders_card(qtbot, app_mock):
    app_mock.ai = FakeAI()
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)
    artifact = CopilotArtifact(
        identifier=1,
        type="songs",
        title="Night Songs",
        songs=[
            SongSuggestion(
                title="hello world",
                artists_name="mary",
                description="",
            )
        ],
    )

    overlay.body._chat_box.copilot.artifact_added.emit(artifact)

    qtbot.waitUntil(
        lambda: bool(
            overlay.body._chat_box.history_widget.findChildren(ChatArtifactCard)
        )
    )


def test_ai_chat_renders_song_artifact_after_final_response(qtbot, app_mock):
    app_mock.ai = FakeAI(FakeStreamingCopilot())
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)

    asyncio.run(overlay.body._chat_box.exec_user_query("推荐几首华语经典歌曲"))

    history = overlay.body._chat_box.history_widget
    cards = history.findChildren(ChatArtifactCard)
    tool_events = history.findChildren(ChatToolEventCard)
    assert len(cards) == 1
    assert len(tool_events) == 1
    assert "create_song_suggestions_artifact" in tool_events[0].text()
    assert cards[0].artifact.title == "Night Songs"
    history_text = "\n".join(
        label.toPlainText() for label in history.findChildren(RoundedLabel)
    )
    assert "我为您推荐了这些歌曲" in history_text
    assert "我来" not in history_text
    assert "我来我为您" not in history_text
    tool_event_index = history._history_layout.indexOf(tool_events[0])
    card_index = history._history_layout.indexOf(cards[0])
    assert tool_event_index < card_index
    last_history_widget = history._history_layout.itemAt(
        history._history_layout.count() - 1
    ).widget()
    assert last_history_widget is cards[0]


def test_ai_chat_shows_streaming_status_without_pre_tool_text(qtbot, app_mock):
    copilot = PausedStreamingCopilot()
    app_mock.ai = FakeAI(copilot)
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)

    async def run_query():
        task = asyncio.create_task(
            overlay.body._chat_box.exec_user_query("推荐几首华语经典歌曲")
        )
        await asyncio.wait_for(copilot.first_token_seen.wait(), timeout=1)

        history = overlay.body._chat_box.history_widget
        status_cards = history.findChildren(ChatStreamingStatusCard)
        assert len(status_cards) == 1
        assert "AI is writing" in status_cards[0].text()
        history_text = "\n".join(
            label.toPlainText() for label in history.findChildren(RoundedLabel)
        )
        assert "我来" not in history_text

        copilot.resume.set()
        await asyncio.wait_for(task, timeout=1)

    asyncio.run(run_query())

    history = overlay.body._chat_box.history_widget
    assert not history.findChildren(ChatStreamingStatusCard)
    history_text = "\n".join(
        label.toPlainText() for label in history.findChildren(RoundedLabel)
    )
    assert "我为您推荐了这些歌曲" in history_text


def test_ai_chat_does_not_show_pre_tool_streaming_text(qtbot, app_mock):
    app_mock.ai = FakeAI(FakeStreamingCopilot())
    app_mock.ai.radio = None
    app_mock.playlist.list.return_value = []
    parent = QWidget()
    parent.resize(QSize(960, 600))
    parent.show()
    qtbot.addWidget(parent)
    app_mock.size.return_value = parent.size()
    overlay = create_aichat_overlay(app_mock, parent=parent)

    async def run_until_tool():
        chat_box = overlay.body._chat_box
        chat_box.history_widget.add_message("user", "推荐几首华语经典歌曲")
        chat_box._collecting_artifacts = True
        chat_box._pending_artifacts = []
        response_message = ""
        async for token, metadata in chat_box.copilot.astream_user_query("query"):
            node = metadata["langgraph_node"]
            if node == "model":
                for block in token.content_blocks:
                    if block["type"] == "text":
                        response_message += block["text"]
            elif node == "tools":
                chat_box._collecting_artifacts = False
                return response_message

    pre_tool_text = asyncio.run(run_until_tool())
    history = overlay.body._chat_box.history_widget
    history_text = "\n".join(
        label.toPlainText() for label in history.findChildren(RoundedLabel)
    )

    assert pre_tool_text == "我来"
    assert "我来" not in history_text
