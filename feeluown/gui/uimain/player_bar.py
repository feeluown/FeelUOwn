import asyncio
import logging

from PyQt5.QtCore import Qt, QTimer, QRect, QEvent
from PyQt5.QtGui import QFontMetrics, QPainter
from PyQt5.QtWidgets import (
    QApplication, QLabel, QFrame, QHBoxLayout, QVBoxLayout,
    QPushButton, QSizePolicy, QMenu,
)
from feeluown.gui.widgets.cover_label import CoverLabelV2

from feeluown.utils import aio
from feeluown.excs import ProviderIOError
from feeluown.media import MediaType
from feeluown.player import State
from feeluown.gui.widgets.lyric import Window as LyricWindow
from feeluown.gui.widgets.menu import SongMenuInitializer
from feeluown.gui.helpers import resize_font
from feeluown.gui.widgets import TextButton
from feeluown.gui.widgets.playlist_button import PlaylistButton
from feeluown.gui.widgets.volume_button import VolumeButton
from feeluown.gui.widgets.progress_slider import ProgressSlider
from feeluown.gui.widgets.labels import ProgressLabel, DurationLabel

logger = logging.getLogger(__name__)


class LikeButton(QPushButton):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app
        self.setCheckable(True)
        self._app.playlist.song_changed_v2.connect(self.on_song_changed)
        self.clicked.connect(self.toggle_liked)
        self.toggled.connect(self.on_toggled)

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


class WatchButton(TextButton):
    def __init__(self, app, parent):
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


class LyricButton(TextButton):
    def __init__(self, app, parent):
        super().__init__('词', parent=parent)
        self._app = app

        self.setCheckable(True)
        self.clicked.connect(self._toggle_lyric_window)
        self.parent().lyric_window.installEventFilter(self)  # hack

    def _toggle_lyric_window(self):
        lyric_window = self._app.ui.player_bar.lyric_window
        if lyric_window.isVisible():
            lyric_window.hide()
        else:
            lyric_window.show()

    def eventFilter(self, obj, event):
        """Event filter for lyric window"""
        if event.type() == QEvent.Show:
            self.setChecked(True)
        elif event.type() == QEvent.Hide:
            self.setChecked(False)
        return False


class SongBriefLabel(QLabel):
    default_text = '...'

    def __init__(self, app):
        super().__init__(text=self.default_text, parent=None)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._app = app

        # TODO: we can create a label class that roll the text when
        # the text is longer than the label width
        self._timer = QTimer()
        self._txt = self._raw_text = self.default_text
        self._font_metrics = QFontMetrics(QApplication.font())
        self._text_rect = self._font_metrics.boundingRect(self._raw_text)
        # text's position, keep changing to make text roll
        self._pos = 0
        self._timer.timeout.connect(self.change_text_position)

    def change_text_position(self):
        if not self.parent().isVisible():
            self._timer.stop()
            self._pos = 0
            return
        if self._text_rect.width() + self._pos > 0:
            # control the speed of rolling
            self._pos -= 5
        else:
            self._pos = self.width()
        self.update()

    def setText(self, text):
        self._txt = self._raw_text = text
        self._text_rect = self._font_metrics.boundingRect(self._raw_text)
        self._pos = 0
        self.update()

    def enterEvent(self, event):
        # we do not compare text_rect with self_rect here because of
        # https://github.com/feeluown/FeelUOwn/pull/425#discussion_r536817226
        # TODO: find out why
        if self._txt != self._raw_text:
            # decrease to make rolling more fluent
            self._timer.start(150)

    def leaveEvent(self, event):
        self._timer.stop()
        self._pos = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(QApplication.font())
        painter.setPen(self._app.palette().color(self._app.palette().Text))

        if self._timer.isActive():
            self._txt = self._raw_text
        else:
            self._txt = self._font_metrics.elidedText(
                self._raw_text, Qt.ElideRight, self.width())

        painter.drawText(
            QRect(self._pos, 0, self.width() - self._pos, self.height()),
            Qt.AlignLeft | Qt.AlignVCenter,
            self._txt
        )

    def contextMenuEvent(self, e):
        song = self._app.playlist.current_song
        if song is None:
            return

        menu = QMenu()
        SongMenuInitializer(self._app, song).apply(menu)
        menu.exec(e.globalPos())


class SourceLabel(QLabel):
    default_text = '音乐来源'

    def __init__(self, app, parent=None):
        super().__init__(text=SourceLabel.default_text, parent=parent)
        self._app = app

    def contextMenuEvent(self, e):
        # FIXME(wuliaotc): 在切换provider时禁用menu
        song = self._app.playlist.current_song
        if song is None:
            return

        menu = QMenu()
        submenu = menu.addMenu('“智能”替换')
        for provider in self._app.library.list():
            pid = provider.identifier
            if pid == song.source:
                continue
            action = submenu.addAction(provider.name)
            action.triggered.connect(
                (lambda x: lambda: asyncio.create_task(self._switch_provider(x)))(pid)
            )
        menu.exec(e.globalPos())

    async def _switch_provider(self, provider_id):
        song = self._app.playlist.current_song
        songs = await self._app.library.a_list_song_standby(
            song, source_in=[provider_id])
        if songs:
            standby = songs[0]
            assert standby != song
            self._app.show_msg(f'使用 {standby} 替换当前歌曲')
            self._app.playlist.pure_set_current_song(standby, standby.url)
            self._app.playlist.remove(song)
        else:
            self._app.show_msg(f'提供方 “{provider_id}” 没有找到可用的相似歌曲')


class PlayerControlPanel(QFrame):

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        class IconButton(QPushButton):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

        self.lyric_window = LyricWindow()
        self.lyric_window.hide()

        # initialize sub widgets
        self._layout = QHBoxLayout(self)
        self.previous_btn = IconButton(self)
        self.pp_btn = IconButton(self)
        self.next_btn = IconButton(self)

        self.volume_btn = VolumeButton(self)
        self.playlist_btn = PlaylistButton(self._app, self)
        #: mark song as favorite button
        self.like_btn = LikeButton(self._app, self)
        self.mv_btn = TextButton('MV', self)
        self.toggle_lyric_btn = LyricButton(self._app, self)
        self.download_btn = QPushButton(self)
        self.toggle_watch_btn = WatchButton(self._app, self)
        self.toggle_video_btn = TextButton('△', self)
        # toggle picture-in-picture button
        self.toggle_pip_btn = TextButton('◲', self)

        self.previous_btn.setObjectName('previous_btn')
        self.pp_btn.setObjectName('pp_btn')
        self.next_btn.setObjectName('next_btn')
        self.playlist_btn.setObjectName('playlist_btn')
        self.volume_btn.setObjectName('volume_btn')
        self.download_btn.setObjectName('download_btn')
        self.like_btn.setObjectName('like_btn')
        self.mv_btn.setObjectName('mv_btn')
        self.toggle_lyric_btn.setObjectName('toggle_lyric_btn')
        self.toggle_video_btn.setObjectName('toggle_video_btn')
        self.toggle_pip_btn.setObjectName('toggle_pip_btn')

        self.progress_slider = ProgressSlider(app=app, parent=self)

        self.volume_btn.setToolTip('调整音量')
        self.playlist_btn.setToolTip('显示当前播放列表')

        self.mv_btn.setToolTip('播放 MV')
        self.download_btn.setToolTip('下载歌曲（未实现，欢迎 PR）')
        self.pp_btn.setCheckable(True)
        self.download_btn.setCheckable(True)

        self.song_title_label = SongBriefLabel(self._app)
        self.song_title_label.setAlignment(Qt.AlignCenter)
        self.song_source_label = SourceLabel(self._app, parent=self)

        self.cover_label = CoverLabelV2(app)
        self.duration_label = DurationLabel(app, parent=self)
        self.position_label = ProgressLabel(app, parent=self)

        # we should enable focus since we want to have shortcut keys
        self.setFocusPolicy(Qt.StrongFocus)
        self.song_source_label.setObjectName('song_source_label')

        self.next_btn.clicked.connect(self._app.playlist.next)
        self.previous_btn.clicked.connect(self._app.playlist.previous)
        self.pp_btn.clicked.connect(self._app.player.toggle)
        self.volume_btn.change_volume_needed.connect(
            lambda volume: setattr(self._app.player, 'volume', volume))

        player = self._app.player
        playlist = self._app.playlist
        playlist.song_changed.connect(self.on_player_song_changed, aioqueue=True)
        player.state_changed.connect(self._on_player_state_changed, aioqueue=True)
        player.metadata_changed.connect(self.on_metadata_changed, aioqueue=True)
        player.volume_changed.connect(self.volume_btn.on_volume_changed)
        self._app.live_lyric.sentence_changed.connect(self.lyric_window.set_sentence)
        self.lyric_window.play_previous_needed.connect(playlist.previous)
        self.lyric_window.play_next_needed.connect(playlist.next)

        self._setup_ui()

    def _setup_ui(self):
        self.cover_label.setFixedWidth(44)
        self.cover_label.setMaximumHeight(44)
        self.song_source_label.setFixedHeight(20)
        self.progress_slider.setFixedHeight(20)  # half of parent height
        self.position_label.setFixedWidth(50)
        self.duration_label.setFixedWidth(50)
        self.position_label.setAlignment(Qt.AlignCenter)
        self.duration_label.setAlignment(Qt.AlignCenter)
        self.like_btn.setFixedSize(15, 15)
        self.download_btn.setFixedSize(15, 15)
        self.download_btn.hide()
        self.mv_btn.setFixedHeight(16)
        self.toggle_lyric_btn.setFixedHeight(16)
        self.toggle_watch_btn.setFixedHeight(16)

        self.progress_slider.setSizePolicy(QSizePolicy.Expanding,
                                           QSizePolicy.Preferred)
        self._sub_layout = QVBoxLayout()
        self._sub_top_layout = QHBoxLayout()
        self._progress_v_layout = QVBoxLayout()
        self._cover_v_layout = QVBoxLayout()

        # add space to make top layout align with progress slider
        self._sub_top_layout.addSpacing(3)
        self._sub_top_layout.addWidget(self.song_source_label)
        self._sub_top_layout.addSpacing(5)
        self._sub_top_layout.addWidget(self.song_title_label)
        self._sub_top_layout.addSpacing(5)
        self._sub_top_layout.addWidget(self.like_btn)
        self._sub_top_layout.addSpacing(8)
        self._sub_top_layout.addWidget(self.mv_btn)
        self._sub_top_layout.addSpacing(8)
        self._sub_top_layout.addWidget(self.toggle_lyric_btn)
        self._sub_top_layout.addSpacing(8)
        self._sub_top_layout.addWidget(self.toggle_watch_btn)
        # self._sub_top_layout.addSpacing(8)
        # self._sub_top_layout.addWidget(self.download_btn)
        self._sub_top_layout.addSpacing(3)

        self._sub_layout.addSpacing(3)
        self._sub_layout.addStretch(0)
        self._sub_layout.addLayout(self._sub_top_layout)
        self._sub_layout.addStretch(0)
        self._sub_layout.addWidget(self.progress_slider)
        self._sub_layout.addStretch(0)

        self._progress_v_layout.addStretch(0)
        self._progress_v_layout.addWidget(self.position_label)
        self._progress_v_layout.addSpacing(3)
        self._progress_v_layout.addWidget(self.duration_label)
        self._progress_v_layout.addStretch(0)

        # Put the cover_label in a vboxlayout and add strech around it,
        # so that cover_label's sizehint is respected.
        self._cover_v_layout.addStretch(0)
        self._cover_v_layout.addWidget(self.cover_label)
        self._cover_v_layout.addStretch(0)

        self._layout.addSpacing(20)
        self._layout.addWidget(self.previous_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.pp_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.next_btn)
        self._layout.addSpacing(26)
        self._layout.addWidget(self.volume_btn)
        # 18 = 200(left_panel_width) - 4 * 30(btn) - 20 - 8 - 8 -26
        self._layout.addSpacing(18)
        self._layout.addStretch(0)
        self._layout.addLayout(self._cover_v_layout)
        self._layout.addSpacing(7)
        self._layout.addLayout(self._sub_layout)
        self._layout.setStretchFactor(self._sub_layout, 1)
        self._layout.addSpacing(7)
        self._layout.addLayout(self._progress_v_layout)
        self._layout.addStretch(0)
        self._layout.addSpacing(18)
        self._layout.addWidget(self.playlist_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.toggle_video_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.toggle_pip_btn)
        self._layout.addSpacing(18)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def on_player_song_changed(self, song):
        task_spec = self._app.task_mgr.get_or_create('update-mv-btn-status')
        task_spec.bind_coro(self.update_mv_btn_status(song))

    def on_metadata_changed(self, metadata):
        if not metadata:
            self.song_source_label.setText('歌曲来源')
            self.song_title_label.setText('')
            return

        # Set main text.
        text = metadata.get('title', '')
        if text:
            artists = metadata.get('artists', [])
            if artists:
                # FIXME: use _get_artists_name
                text += f" - {','.join(artists)}"
        self.song_title_label.setText(text)

        # Set source name.
        source = metadata.get('source', '')
        default = '未知来源'

        if source:
            source_name_map = {p.identifier: p.name
                               for p in self._app.library.list()}
            name = source_name_map.get(source, default)
            self.song_source_label.setText(name)
        else:
            self.song_source_label.setText(default)

        # Set song artwork.
        artwork = metadata.get('artwork', '')
        artwork_uid = metadata.get('uri', artwork)
        if artwork:
            aio.run_afn(self.cover_label.show_cover, artwork, artwork_uid)

        # Set audio bitrate info if available.
        media = self._app.player.current_media
        if media is not None and media.type_ == MediaType.audio:
            props = media.props
            if props.bitrate:
                text = self.song_source_label.text()
                self.song_source_label.setText(f'{text} - {props.bitrate}kbps')

    async def update_mv_btn_status(self, song):
        if song is None:
            self.mv_btn.setEnabled(False)
            return

        try:
            mv = await aio.run_fn(self._app.library.song_get_mv, song)
        except ProviderIOError:
            logger.exception('fetch song mv info failed')
            self.mv_btn.setEnabled(False)
        else:
            if mv is None:
                self.mv_btn.setEnabled(False)
            else:
                self.mv_btn.setToolTip(mv.title)
                self.mv_btn.setEnabled(True)

    def _on_player_state_changed(self, state):
        self.pp_btn.setChecked(state == State.playing)


class TopPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.pc_panel = PlayerControlPanel(self._app, self)
        self.setObjectName('top_panel')

        self.setFixedHeight(60)

        self._layout.addWidget(self.pc_panel)
