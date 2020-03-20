import asyncio
import logging

from PyQt5.QtCore import Qt, QTime, pyqtSignal, QSize
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QSizePolicy,
    QSlider,
)

from fuocore.excs import ProviderIOError
from fuocore.media import MediaType
from fuocore.utils import parse_ms
from fuocore.player import PlaybackMode, State
from feeluown.helpers import async_run
from feeluown.widgets.volume_button import VolumeButton

logger = logging.getLogger(__name__)


class ProgressSlider(QSlider):
    pause_player_needed = pyqtSignal()
    resume_player_needed = pyqtSignal()
    change_position_needed = pyqtSignal([int])

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setOrientation(Qt.Horizontal)
        self.sliderPressed.connect(self._on_pressed)
        self.sliderReleased.connect(self._on_released)

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(360, size.height())

    def _on_pressed(self):
        self.pause_player_needed.emit()

    def _on_released(self):
        self.change_position_needed.emit(self.value())
        self.resume_player_needed.emit()

    def set_duration(self, ms):
        self.setRange(0, ms / 1000)

    def update_state(self, ms):
        self.setValue(ms / 1000)


class PlayerControlPanel(QFrame):

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        class IconButton(QPushButton):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

        self._playback_modes = list(PlaybackMode.__members__.values())
        self._pm_alias_map = {
            PlaybackMode.one_loop: '单曲循环',
            PlaybackMode.sequential: '顺序播放',
            PlaybackMode.loop: '循环播放',
            PlaybackMode.random: '随机播放',
        }

        # initialize sub widgets
        self._layout = QHBoxLayout(self)
        self.previous_btn = IconButton(self)
        self.pp_btn = IconButton(self)
        self.next_btn = IconButton(self)

        #: playback mode switch button
        self.pms_btn = QPushButton(self)
        self.volume_btn = VolumeButton(self)
        self.playlist_btn = IconButton(parent=self)
        #: mark song as favorite button
        self.like_btn = QPushButton(self)
        self.mv_btn = QPushButton('MV', self)
        self.download_btn = QPushButton(self)
        self.toggle_video_btn = QPushButton('△', self)

        self.previous_btn.setObjectName('previous_btn')
        self.pp_btn.setObjectName('pp_btn')
        self.next_btn.setObjectName('next_btn')
        self.playlist_btn.setObjectName('playlist_btn')
        self.volume_btn.setObjectName('volume_btn')
        self.pms_btn.setObjectName('pms_btn')
        self.download_btn.setObjectName('download_btn')
        self.like_btn.setObjectName('like_btn')
        self.mv_btn.setObjectName('mv_btn')
        self.toggle_video_btn.setObjectName('toggle_video_btn')

        self.progress_slider = ProgressSlider(self)

        self.pms_btn.setToolTip('修改播放模式')
        self.volume_btn.setToolTip('调整音量')
        self.playlist_btn.setToolTip('显示当前播放列表')
        self.progress_slider.setToolTip('拖动调节进度')

        self.mv_btn.setToolTip('播放 MV')
        self.download_btn.setToolTip('下载歌曲（未实现，欢迎 PR）')
        self.like_btn.setToolTip('收藏歌曲（未实现，欢迎 PR）')
        self.pp_btn.setCheckable(True)
        self.like_btn.setCheckable(True)
        self.download_btn.setCheckable(True)
        self.toggle_video_btn.hide()

        self.song_title_label = QLabel('No song is playing.', parent=self)
        self.song_source_label = QLabel('歌曲来源', parent=self)
        self.song_title_label.setAlignment(Qt.AlignCenter)
        self.duration_label = QLabel('00:00', parent=self)
        self.position_label = QLabel('00:00', parent=self)

        self.song_source_label.setObjectName('song_source_label')

        self.next_btn.clicked.connect(self._app.playlist.next)
        self.previous_btn.clicked.connect(self._app.playlist.previous)
        self.pp_btn.clicked.connect(self._app.player.toggle)
        self.pms_btn.clicked.connect(self._switch_playback_mode)
        self.volume_btn.change_volume_needed.connect(
            lambda volume: setattr(self._app.player, 'volume', volume))

        player = self._app.player

        player.state_changed.connect(self._on_player_state_changed, aioqueue=True)
        player.position_changed.connect(self.on_position_changed)
        player.duration_changed.connect(self.on_duration_changed, aioqueue=True)
        player.playlist.playback_mode_changed.connect(
            self.on_playback_mode_changed, aioqueue=True)
        player.playlist.song_changed.connect(
            self.on_player_song_changed, aioqueue=True)
        player.media_changed.connect(
            self.on_player_media_changed, aioqueue=True)
        player.volume_changed.connect(self.volume_btn.on_volume_changed)
        self.progress_slider.resume_player_needed.connect(player.resume)
        self.progress_slider.pause_player_needed.connect(player.pause)
        self.progress_slider.change_position_needed.connect(
            lambda value: setattr(player, 'position', value))

        self._update_pms_btn_text()
        self._setup_ui()

    def _setup_ui(self):
        # set widget layout
        self.song_source_label.setFixedHeight(20)
        self.progress_slider.setFixedHeight(20)  # half of parent height
        self.position_label.setFixedWidth(45)
        self.duration_label.setFixedWidth(45)
        # on macOS, we should set AlignVCenter flag
        self.position_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.like_btn.setFixedSize(15, 15)
        self.download_btn.setFixedSize(15, 15)
        self.mv_btn.setFixedHeight(16)

        self.progress_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._sub_layout = QVBoxLayout()
        self._sub_top_layout = QHBoxLayout()

        # add space to make top layout align with progress slider
        self._sub_top_layout.addSpacing(3)
        self._sub_top_layout.addWidget(self.song_source_label)
        self._sub_top_layout.addSpacing(5)
        self._sub_top_layout.addWidget(self.song_title_label)
        self._sub_top_layout.addSpacing(5)
        self._sub_top_layout.addStretch(0)
        self._sub_top_layout.addWidget(self.like_btn)
        self._sub_top_layout.addSpacing(8)
        self._sub_top_layout.addWidget(self.mv_btn)
        self._sub_top_layout.addSpacing(8)
        self._sub_top_layout.addWidget(self.download_btn)
        self._sub_top_layout.addSpacing(3)

        self._sub_layout.addSpacing(3)
        self._sub_layout.addLayout(self._sub_top_layout)
        self._sub_layout.addWidget(self.progress_slider)

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
        self._layout.addWidget(self.position_label)
        self._layout.addSpacing(7)
        self._layout.addLayout(self._sub_layout)
        self._layout.setStretchFactor(self._sub_layout, 1)
        self._layout.addSpacing(7)
        self._layout.addWidget(self.duration_label)
        self._layout.addStretch(0)
        self._layout.addSpacing(18)
        self._layout.addWidget(self.pms_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.playlist_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.toggle_video_btn)
        self._layout.addSpacing(18)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def _switch_playback_mode(self):
        playlist = self._app.player.playlist
        pm_total = len(self._playback_modes)
        pm_idx = self._playback_modes.index(playlist.playback_mode)
        if pm_idx < pm_total - 1:
            pm_idx += 1
        else:
            pm_idx = 0
        playlist.playback_mode = self._playback_modes[pm_idx]

    def on_duration_changed(self, duration):
        duration = duration * 1000
        m, s = parse_ms(duration)
        t = QTime(0, m, s)
        self.progress_slider.set_duration(duration)
        self.duration_label.setText(t.toString('mm:ss'))

    def on_position_changed(self, position):
        if position is None:
            return
        position = position * 1000
        m, s = parse_ms(position)
        t = QTime(0, m, s)
        self.position_label.setText(t.toString('mm:ss'))
        self.progress_slider.update_state(position)

    def on_playback_mode_changed(self, playback_mode):
        self._update_pms_btn_text()

    def _update_pms_btn_text(self):
        playback_mode = self._app.player.playlist.playback_mode
        alias = self._pm_alias_map[playback_mode]
        self.pms_btn.setText(alias)

    def on_player_song_changed(self, song):
        if song is None:
            self.song_source_label.setText('歌曲来源')
            self.song_title_label.setText('No song is playing.')
            return
        source_name_map = {p.identifier: p.name
                           for p in self._app.library.list()}
        font_metrics = QFontMetrics(QApplication.font())
        text = '{} - {}'.format(song.title_display, song.artists_name_display)
        # width -> three button + source label + text <= progress slider
        # three button: 63, source label: 150
        elided_text = font_metrics.elidedText(
            text, Qt.ElideRight, self.progress_slider.width() - 200)
        self.song_source_label.setText(source_name_map[song.source])
        self.song_title_label.setText(elided_text)
        loop = asyncio.get_event_loop()
        loop.create_task(self.update_mv_btn_status(song))

    def on_player_media_changed(self, media):
        if media is not None and media.type_ == MediaType.audio:
            metadata = media.metadata
            if metadata.bitrate:
                text = self.song_source_label.text()
                bitrate_text = str(metadata.bitrate) + 'kbps'
                self.song_source_label.setText(
                    '{} - {}'.format(text, bitrate_text))

    async def update_mv_btn_status(self, song):
        try:
            mv = await async_run(lambda: song.mv)
        except ProviderIOError:
            logger.exception('fetch song mv info failed')
            self.mv_btn.setEnabled(False)
        else:
            if mv:
                self.mv_btn.setToolTip(mv.name)
                self.mv_btn.setEnabled(True)
            else:
                self.mv_btn.setEnabled(False)

    def _on_player_state_changed(self, state):
        self.pp_btn.setChecked(state == State.playing)
