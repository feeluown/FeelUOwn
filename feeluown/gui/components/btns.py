import logging
from typing import TYPE_CHECKING

from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QPushButton, QWidget, QHBoxLayout
from feeluown.gui.widgets.selfpaint_btn import TriagleButton

from feeluown.player import State
from feeluown.excs import ProviderIOError
from feeluown.utils.aio import run_fn
from feeluown.gui.widgets.textbtn import TextButton
from feeluown.gui.widgets import PlayPauseButton, PlayNextButton, PlayPreviousButton
from feeluown.gui.helpers import resize_font

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


class LyricButton(TextButton):
    def __init__(self, app: 'GuiApp', **kwargs):
        kwargs.setdefault('height', 16)
        super().__init__('词', **kwargs)
        self._app = app

        font_size = 9
        self.setCheckable(True)
        self.clicked.connect(self._toggle_lyric_window)
        font = self.font()
        font.setPixelSize(font_size)
        self.setFont(font)

        self._app.ui.lyric_window.installEventFilter(self)

    def _toggle_lyric_window(self):
        lyric_window = self._app.ui.lyric_window
        if lyric_window.isVisible():
            lyric_window.hide()
        else:
            lyric_window.show()

    def eventFilter(self, _, event):
        """Event filter for lyric window"""
        if event.type() == QEvent.Show:
            self.setChecked(True)
        elif event.type() == QEvent.Hide:
            self.setChecked(False)
        return False


class WatchButton(TextButton):
    def __init__(self, app: 'GuiApp', *args, **kwargs):
        super().__init__('♨', *args, **kwargs)
        self._app = app

        self.setToolTip('开启 watch 模式时，播放器会优先尝试为歌曲找一个合适的视频来播放。\n'
                        '最佳实践：开启 watch 的同时建议开启视频的画中画模式。')

        self.setCheckable(True)
        self._setup_ui()
        self.clicked.connect(self.on_clicked)

    def on_clicked(self):
        self._app.playlist.watch_mode = not self._app.playlist.watch_mode
        # Assume that playlist.watch_mode will only be changed by WatchButton
        if self._app.playlist.watch_mode is True:
            self.setChecked(True)
        else:
            self.setChecked(False)

    def _setup_ui(self):
        font = self.font()
        resize_font(font, -2)
        self.setFont(font)

    def showEvent(self, e):
        self.setChecked(self._app.playlist.watch_mode)
        super().showEvent(e)


class LikeButton(QPushButton):
    def __init__(self, app: 'GuiApp', size=(15, 15), parent=None):
        super().__init__(parent=parent)
        self._app = app
        self.setCheckable(True)
        self.setFixedSize(*size)

        self._app.playlist.song_changed_v2.connect(self.on_song_changed)
        self.clicked.connect(self.toggle_liked)
        self.toggled.connect(self.on_toggled)
        self.setObjectName('like_btn')

    def on_song_changed(self, song, media):
        if song is not None:
            self.setChecked(self.is_song_liked(song))

    def toggle_liked(self):
        song = self._app.playlist.current_song
        coll_library = self._app.coll_mgr.get_coll_library()
        if self.is_song_liked(song):
            coll_library.remove(song)
            self._app.show_msg('歌曲已经从“本地收藏”中移除')
        else:
            coll_library.add(song)
            self._app.show_msg('歌曲已经添加到“本地收藏”')

    def on_toggled(self):
        song = self._app.playlist.current_song
        if self.is_song_liked(song):
            self.setToolTip('添加到“本地收藏”')
        else:
            self.setToolTip('从“本地收藏”中移除')

    def is_song_liked(self, song):
        coll_library = self._app.coll_mgr.get_coll_library()
        return song in coll_library.models


class SongMVTextButton(TextButton):
    def __init__(self, app: 'GuiApp', song=None, text='MV', **kwargs):
        super().__init__(text, **kwargs)
        self._app = app
        self._song = None
        self._mv = None

        self.bind_song(song)
        self.setDisabled(True)
        self.clicked.connect(self.on_clicked)

    def on_clicked(self):
        if self._mv is not None:
            self._app.watch_mgr.play_video(self._mv)

    def bind_song(self, song):
        if song != self._song:
            self._song = song
            self._mv = None

    async def get_mv(self):
        if self._song is None:
            return None

        try:
            mv = await run_fn(self._app.library.song_get_mv, self._song)
        except ProviderIOError:
            logger.exception('get song mv info failed')
            mv = None
            self.setEnabled(False)
        else:
            if mv is None:
                self.setEnabled(False)
            else:
                self.setToolTip(mv.title)
                self.setEnabled(True)
        self._mv = mv
        return self._mv


class NowplayingMVTextButton(SongMVTextButton):
    def __init__(self, app: 'GuiApp', parent=None, **kwargs):
        super().__init__(app, song=None, parent=parent, **kwargs)

        self.setObjectName('mv_btn')
        self._app.playlist.song_mv_changed.connect(
            self.on_song_mv_changed, aioqueue=True)

    def on_song_mv_changed(self, _, mv):
        self.setEnabled(mv is not None)
        self._mv = mv


class MediaButtonsV2(QWidget):
    def __init__(self, app: 'GuiApp', button_width=30, spacing=0, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.previous_btn = PlayPreviousButton(parent=self, length=button_width)
        self.pp_btn = PlayPauseButton(parent=self, length=button_width)
        self.next_btn = PlayNextButton(parent=self, length=button_width)
        self.toggle_video_btn = TriagleButton(length=button_width)
        self.toggle_video_btn.hide()
        self.pp_btn.setCheckable(True)
        self.toggle_video_btn.setToolTip('展示视频画面')

        self._layout = QHBoxLayout(self)
        self._layout.setSpacing(spacing)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.previous_btn)
        self._layout.addWidget(self.pp_btn)
        self._layout.addWidget(self.next_btn)
        self._layout.addWidget(self.toggle_video_btn)

        self.next_btn.clicked.connect(self._app.playlist.next)
        self.previous_btn.clicked.connect(self._app.playlist.previous)
        self.pp_btn.clicked.connect(self._app.player.toggle)
        self._app.player.state_changed.connect(
            self._on_player_state_changed, aioqueue=True
        )
        self._app.player.video_format_changed.connect(
            self.on_video_format_changed, aioqueue=True
        )

    def _on_player_state_changed(self, state):
        self.pp_btn.setChecked(state == State.playing)

    def on_video_format_changed(self, video_format):
        if video_format is None:
            self.toggle_video_btn.hide()
        else:
            self.toggle_video_btn.show()
