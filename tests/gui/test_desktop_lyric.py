"""
Tests for the standalone (desktop) lyric window.

See: https://github.com/feeluown/FeelUOwn/issues/1019
"""
from collections import OrderedDict
from unittest.mock import MagicMock

import pytest
from PyQt6.QtCore import Qt, QEvent, QPointF, QPoint
from PyQt6.QtGui import QColor, QFont, QPalette, QMouseEvent
from PyQt6.QtWidgets import QApplication

from feeluown.gui.components.desktop_lyric import DesktopLyricView
from feeluown.gui.uimain.lyric import (
    HEIGHT_LINE_OPTIONS,
    InnerLyricWindow,
    LyricWindow,
)
from feeluown.player import Lyric, LyricLine


def _make_lyric(texts, active_index=0):
    pos_s_map = OrderedDict()
    for i, text in enumerate(texts):
        pos_s_map[i * 1000] = text
    lyric = Lyric(pos_s_map)
    if active_index > 0:
        lyric.update_position(active_index)
    return lyric


def _build_app_mock():
    app = MagicMock()
    app.live_lyric = MagicMock()
    app.live_lyric.line_changed = MagicMock()
    app.live_lyric.lyrics_changed = MagicMock()
    app.live_lyric.current_line = LyricLine("...", "", False)
    app.live_lyric.current_lyrics = (None, None)
    return app


def test_desktop_lyric_view_renders_lines(qtbot):
    app = _build_app_mock()
    view = DesktopLyricView(app)
    qtbot.addWidget(view)
    lyric = _make_lyric(["alpha", "bravo", "charlie"], active_index=1)
    view.set_lyric(lyric)
    assert view.count() == 3
    view.on_line_changed(LyricLine("bravo", "", False))
    assert view.currentRow() == 1


def test_desktop_lyric_view_handles_none_lyric(qtbot):
    app = _build_app_mock()
    view = DesktopLyricView(app)
    qtbot.addWidget(view)
    view.on_lyric_changed(None, None)
    assert view.count() == 1
    assert view.currentRow() == 0


def test_desktop_lyric_view_highlight_color_follows_text_color(qtbot):
    app = _build_app_mock()
    view = DesktopLyricView(app)
    qtbot.addWidget(view)
    palette = QPalette(view.palette())
    palette.setColor(QPalette.ColorRole.Text, QColor("red"))
    view.setPalette(palette)
    assert view.palette().color(QPalette.ColorRole.HighlightedText) == QColor("red")


def test_desktop_lyric_view_background_stays_transparent(qtbot):
    app = _build_app_mock()
    view = DesktopLyricView(app)
    qtbot.addWidget(view)
    palette = QPalette(view.palette())
    palette.setColor(QPalette.ColorRole.Text, QColor("white"))
    palette.setColor(QPalette.ColorRole.Window, QColor("black"))
    palette.setColor(QPalette.ColorRole.Base, QColor("black"))
    view.setPalette(palette)
    assert view.palette().color(QPalette.ColorRole.Window) == Qt.GlobalColor.transparent
    assert view.palette().color(QPalette.ColorRole.Base) == Qt.GlobalColor.transparent


def test_desktop_lyric_view_initial_palette_is_transparent(qtbot):
    app = _build_app_mock()
    view = DesktopLyricView(app)
    qtbot.addWidget(view)
    palette = view.palette()
    assert palette.color(QPalette.ColorRole.Window) == Qt.GlobalColor.transparent
    assert palette.color(QPalette.ColorRole.Base) == Qt.GlobalColor.transparent
    assert palette.color(QPalette.ColorRole.Highlight) == Qt.GlobalColor.transparent
    assert palette.color(QPalette.ColorRole.AlternateBase) == Qt.GlobalColor.transparent


def test_desktop_lyric_view_items_have_vertical_spacing(qtbot):
    app = _build_app_mock()
    view = DesktopLyricView(app)
    qtbot.addWidget(view)
    lyric = _make_lyric(["alpha", "bravo", "charlie"], active_index=0)
    view.set_lyric(lyric)
    for i in range(view.count()):
        item = view.item(i)
        size_hint = item.data(Qt.ItemDataRole.UserRole)
        assert size_hint is not None
        assert size_hint.height() > 0


def test_desktop_lyric_view_set_font_does_not_raise(qtbot):
    app = _build_app_mock()
    view = DesktopLyricView(app)
    qtbot.addWidget(view)
    font = QFont(view.font())
    font.setPixelSize(24)
    view.setFont(font)
    assert view.font().pixelSize() == 24


def test_lyric_window_dump_state_includes_height_lines(qtbot):
    app = _build_app_mock()
    win = LyricWindow(app)
    qtbot.addWidget(win)
    win._inner.set_height_lines(5, refresh=False)
    state = win.dump_state()
    assert state["height_lines"] == 5


def test_lyric_window_dump_apply_state_roundtrip(qtbot):
    app = _build_app_mock()
    win = LyricWindow(app)
    qtbot.addWidget(win)
    win.resize(420, 180)
    win._inner.set_height_lines(5, refresh=False)
    state = win.dump_state()

    win2 = LyricWindow(app)
    qtbot.addWidget(win2)
    win2.apply_state(state)
    assert win2._inner.height_lines == 5
    assert win2._inner.height_lines == state["height_lines"]
    assert win2.height() == state["geometry"][3]


def test_lyric_window_apply_state_uses_saved_height_lines(qtbot):
    app = _build_app_mock()
    win = LyricWindow(app)
    qtbot.addWidget(win)
    expected_lines = 5
    win._inner.set_height_lines(expected_lines, refresh=True)
    height_with_5 = win.height()
    state = win.dump_state()
    assert state["height_lines"] == expected_lines

    win2 = LyricWindow(app)
    qtbot.addWidget(win2)
    win2.apply_state(state)
    assert win2._inner.height_lines == expected_lines
    assert win2.height() == height_with_5


def test_lyric_window_apply_state_is_backward_compatible(qtbot):
    app = _build_app_mock()
    win = LyricWindow(app)
    qtbot.addWidget(win)
    legacy_state = {
        "geometry": (10, 20, 400, 120),
        "font": win._inner.font().toString(),
        "bg": "#ff202020",
        "fg": "#ffffffff",
    }
    win.apply_state(legacy_state)
    # Legacy state without auto_resize defaults to single-line mode.
    assert win._inner.auto_resize is True
    assert win._inner._height_lines == 1
    assert win._inner._size_grip.isHidden()


def test_set_height_lines_clamps_to_minimum(qtbot):
    app = _build_app_mock()
    inner = InnerLyricWindow(app)
    qtbot.addWidget(inner)
    inner.set_height_lines(0, refresh=False)
    assert inner.height_lines == 1


@pytest.mark.parametrize("n", HEIGHT_LINE_OPTIONS)
def test_set_height_lines_accepts_known_options(qtbot, n):
    app = _build_app_mock()
    inner = InnerLyricWindow(app)
    qtbot.addWidget(inner)
    inner.set_height_lines(n, refresh=False)
    assert inner.height_lines == n


def test_zoom_reflows_window_height(qtbot):
    app = _build_app_mock()
    inner = InnerLyricWindow(app)
    qtbot.addWidget(inner)
    inner.set_height_lines(3, refresh=True)
    initial_inner_height = inner.height()
    inner.zoomin()
    inner.zoomin()
    assert inner.height() > initial_inner_height


def test_desktop_lyric_view_set_font_refreshes_item_sizes(qtbot):
    app = _build_app_mock()
    view = DesktopLyricView(app)
    qtbot.addWidget(view)
    lyric = _make_lyric(["alpha", "bravo", "charlie"], active_index=0)
    view.set_lyric(lyric)
    before = view.item(1).sizeHint().height()
    font = QFont(view.font())
    font.setPixelSize(40)
    view.setFont(font)
    after = view.item(1).sizeHint().height()
    assert after > before
    assert view.item(1).data(Qt.ItemDataRole.UserRole) is not None


def test_lyric_window_default_auto_resize_is_true(qtbot):
    app = _build_app_mock()
    win = LyricWindow(app)
    qtbot.addWidget(win)
    assert win._inner.auto_resize is True
    assert win._inner._size_grip.isHidden()


def test_set_height_lines_switches_mode(qtbot):
    app = _build_app_mock()
    inner = InnerLyricWindow(app)
    qtbot.addWidget(inner)
    # Default is single-line mode
    assert inner.auto_resize is True
    assert inner._size_grip.isHidden()
    # Switch to multi-line mode (3 lines)
    inner.set_height_lines(3)
    assert inner.auto_resize is False
    assert not inner._size_grip.isHidden()
    # Switch back to single-line mode (1 line)
    inner.set_height_lines(1)
    assert inner.auto_resize is True
    assert inner._size_grip.isHidden()


def test_dump_state_includes_auto_resize(qtbot):
    app = _build_app_mock()
    win = LyricWindow(app)
    qtbot.addWidget(win)
    state = win.dump_state()
    assert "auto_resize" in state
    assert state["auto_resize"] is True


def test_apply_state_restores_auto_resize(qtbot):
    app = _build_app_mock()
    win = LyricWindow(app)
    qtbot.addWidget(win)
    win._inner.set_height_lines(3)  # switch to multi-line
    state = win.dump_state()
    assert state["auto_resize"] is False
    assert state["height_lines"] == 3

    win2 = LyricWindow(app)
    qtbot.addWidget(win2)
    win2.apply_state(state)
    assert win2._inner.auto_resize is False
    assert not win2._inner._size_grip.isHidden()


def test_apply_state_backward_compatible_auto_resize(qtbot):
    """Legacy state without auto_resize should default to True."""
    app = _build_app_mock()
    win = LyricWindow(app)
    qtbot.addWidget(win)
    legacy_state = {
        "geometry": (10, 20, 400, 120),
        "font": win._inner.font().toString(),
        "bg": "#ff202020",
        "fg": "#ffffffff",
        "height_lines": 3,
    }
    win.apply_state(legacy_state)
    assert win._inner.auto_resize is True


def test_lyric_window_event_filter_installed(qtbot):
    app = _build_app_mock()
    win = LyricWindow(app)
    qtbot.addWidget(win)
    # The event filter should be installed on the viewport
    viewport = win._inner.lyric_view.viewport()
    # Verify by checking that mouse events on the viewport
    # set _old_pos on the window (the event filter handles this)
    pos = viewport.mapToGlobal(QPoint(10, 10))
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(viewport.mapFromGlobal(pos)),
        QPointF(pos),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(viewport, event)
    assert win._old_pos is not None


def test_auto_resize_on_line_changed(qtbot):
    app = _build_app_mock()
    win = LyricWindow(app)
    qtbot.addWidget(win)
    win._inner._auto_resize = True
    win.show()
    initial_width = win.width()
    # Simulate a line_changed with a long text
    lyric = _make_lyric(["a" * 200], active_index=0)
    win._inner.lyric_view.set_lyric(lyric)
    win._inner._on_line_changed(LyricLine("a" * 200, "", False))
    # Window should have resized to accommodate the long text
    assert win.width() >= initial_width
