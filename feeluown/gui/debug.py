import asyncio
from contextlib import contextmanager
import os
from types import SimpleNamespace

from PyQt6.QtCore import QDir, QTimer
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QWidget

from feeluown.debug import *  # noqa
from feeluown.player import State
from feeluown.player.lyric import Line
from feeluown.utils.compat import DefaultQEventLoopPolicy
from feeluown.utils.dispatch import Signal


_MINI_PLAYER_DEBUG_LYRICS = [
    "Drag this mini player around",
    "Right-click anywhere to exit",
    "Hover to show controls",
    "Use arrow keys after focusing it",
]


@contextmanager
def simple_qapp():
    qapp = QApplication([])
    yield qapp
    qapp.exec()


@contextmanager
def async_simple_qapp():
    app_close_event = asyncio.Event()
    qapp = QApplication([])
    qapp.aboutToQuit.connect(app_close_event.set)
    yield qapp
    asyncio.set_event_loop_policy(DefaultQEventLoopPolicy())
    asyncio.run(app_close_event.wait())


def read_dark_theme_qss():
    from feeluown.gui.theme import read_resource

    pkg_root_dir = os.path.join(os.path.dirname(__file__), "..")
    icons_dir = os.path.join(pkg_root_dir, "gui/assets/icons")
    QDir.addSearchPath("icons", icons_dir)

    qss = read_resource("common.qss")
    dark = read_resource("dark.qss")
    return qss + "\n" + dark


@contextmanager
def simple_layout(cls=QHBoxLayout, theme="", aio=False):
    func = async_simple_qapp if aio is True else simple_qapp
    with func():
        main = QWidget()
        if theme == "dark":
            main.setStyleSheet(read_dark_theme_qss())
        layout = cls(main)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        yield layout
        main.show()


class _MiniPlayerDebugPlayer:
    def __init__(self):
        self.metadata_changed = Signal()
        self.state_changed = Signal()
        self.volume_changed = Signal()
        self.position_changed = Signal()
        self.duration_changed = Signal()
        self.current_metadata = {
            "title": "Debug Song",
            "artists": ["FeelUOwn"],
            "artwork": "",
            "source": "",
        }
        self.state = State.playing
        self.position = 12
        self.duration = 180
        self.volume = 50

    def toggle(self):
        if self.state == State.playing:
            self.state = State.paused
        else:
            self.state = State.playing
        self.state_changed.emit(self.state)

    def resume(self):
        self.state = State.playing
        self.state_changed.emit(self.state)


class _MiniPlayerDebugPlaylist:
    def __init__(self):
        self.current_song = None
        self.play_model_stage_changed = Signal()

    def previous(self):
        print("previous")

    def next(self):
        print("next")


class _MiniPlayerDebugLiveLyric:
    def __init__(self):
        self.line_changed = Signal()
        self.current_line = Line("Debug lyric line", "", False)


def create_mini_player_debug_app():
    return SimpleNamespace(
        player=_MiniPlayerDebugPlayer(),
        playlist=_MiniPlayerDebugPlaylist(),
        live_lyric=_MiniPlayerDebugLiveLyric(),
        library=SimpleNamespace(get=lambda _source: None),
    )


def start_mini_player_debug_updates(app, parent):
    def update_line():
        player = app.player
        player.position = (player.position + 5) % player.duration
        player.position_changed.emit(player.position)
        lyric = _MINI_PLAYER_DEBUG_LYRICS[
            (player.position // 5) % len(_MINI_PLAYER_DEBUG_LYRICS)
        ]
        app.live_lyric.current_line = Line(lyric, "", False)
        app.live_lyric.line_changed.emit(app.live_lyric.current_line)

    timer = QTimer(parent)
    timer.timeout.connect(update_line)
    timer.start(1200)
    return timer
