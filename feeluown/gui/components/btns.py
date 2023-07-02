import logging

from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QPushButton, QWidget, QHBoxLayout

from feeluown.app import App
from feeluown.player import State
from feeluown.excs import ProviderIOError
from feeluown.utils import aio
from feeluown.gui.widgets.textbtn import TextButton
from feeluown.gui.helpers import resize_font

logger = logging.getLogger(__name__)


class LyricButton(TextButton):
    def __init__(self, app: App, parent=None):
        super().__init__('词', parent=parent)
        self._app = app

        # TODO: height and font_size should be a arguement of TextButton.
        height = 16
        font_size = 9

        self.setCheckable(True)
        self.clicked.connect(self._toggle_lyric_window)
        self.setFixedHeight(height)
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
    def __init__(self, app: App, parent=None):
        super().__init__('♨', parent=parent)
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


class LikeButton(QPushButton):
    def __init__(self, app: App, size=(15, 15), parent=None):
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
        coll_library = self._app.coll_uimgr.get_coll_library()
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
        coll_library = self._app.coll_uimgr.get_coll_library()
        return song in coll_library.models


class MVButton(TextButton):
    def __init__(self, app: App, parent=None, height=None, **kwargs):
        super().__init__('MV', parent=parent)

        self._app = app
        self.setObjectName('mv_btn')
        self.setToolTip('播放 MV')
        if height:
            self.setFixedHeight(height)

        self._app.playlist.song_changed.connect(self.on_player_song_changed,
                                                aioqueue=True)

    def on_player_song_changed(self, song):
        task_spec = self._app.task_mgr.get_or_create('update-mv-btn-status')
        task_spec.bind_coro(self.update_mv_btn_status(song))

    async def update_mv_btn_status(self, song):
        if song is None:
            self.setEnabled(False)
            return

        try:
            mv = await aio.run_fn(self._app.library.song_get_mv, song)
        except ProviderIOError:
            logger.exception('fetch song mv info failed')
            self.setEnabled(False)
        else:
            if mv is None:
                self.setEnabled(False)
            else:
                self.setToolTip(mv.title)
                self.setEnabled(True)


class MediaButtons(QWidget):
    def __init__(self, app: App, spacing=8, button_width=30, parent=None):
        super().__init__(parent=parent)

        self._app = app

        self.button_width = button_width

        size = (self.button_width, self.button_width)

        self.previous_btn = QPushButton(self)
        self.pp_btn = QPushButton(self)
        self.next_btn = QPushButton(self)
        self.pp_btn.setCheckable(True)

        self.previous_btn.setFixedSize(*size)
        self.pp_btn.setFixedSize(*size)
        self.next_btn.setFixedSize(*size)

        self.previous_btn.setObjectName('previous_btn')
        self.pp_btn.setObjectName('pp_btn')
        self.next_btn.setObjectName('next_btn')

        self._layout = QHBoxLayout(self)
        self._layout.setSpacing(spacing)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self.previous_btn)
        self._layout.addWidget(self.pp_btn)
        self._layout.addWidget(self.next_btn)

        self.next_btn.clicked.connect(self._app.playlist.next)
        self.previous_btn.clicked.connect(self._app.playlist.previous)
        self.pp_btn.clicked.connect(self._app.player.toggle)
        self._app.player.state_changed.connect(
            self._on_player_state_changed, aioqueue=True)

    def _on_player_state_changed(self, state):
        self.pp_btn.setChecked(state == State.playing)
