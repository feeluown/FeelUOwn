import asyncio
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QLabel, QFrame, QHBoxLayout, QVBoxLayout,
    QPushButton, QSizePolicy, QMenu,
)
from feeluown.gui.widgets.cover_label import CoverLabelV2

from feeluown.utils import aio
from feeluown.media import MediaType
from feeluown.gui.widgets import TextButton
from feeluown.gui.widgets.volume_button import VolumeButton
from feeluown.gui.widgets.progress_slider import ProgressSlider
from feeluown.gui.widgets.labels import ProgressLabel, DurationLabel
from feeluown.gui.components import (
    LineSongLabel, MediaButtons, LyricButton, WatchButton, LikeButton,
    MVButton, PlaylistButton,
)

logger = logging.getLogger(__name__)


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

        # initialize sub widgets
        self._layout = QHBoxLayout(self)

        self.media_btns = MediaButtons(app=self._app, parent=self)
        self.previous_btn = self.media_btns.previous_btn
        self.pp_btn = self.media_btns.pp_btn
        self.next_btn = self.media_btns.next_btn

        self.volume_btn = VolumeButton(self)
        self.playlist_btn = PlaylistButton(self._app, length=30, parent=self)
        #: mark song as favorite button
        self.like_btn = LikeButton(self._app, parent=self)
        self.mv_btn = MVButton(app=self._app, parent=self)
        self.toggle_lyric_btn = LyricButton(self._app, parent=self)
        self.download_btn = QPushButton(self)
        self.toggle_watch_btn = WatchButton(self._app, self)
        self.toggle_video_btn = TextButton('△', self)
        # toggle picture-in-picture button
        self.toggle_pip_btn = TextButton('◲', self)

        self.playlist_btn.setObjectName('playlist_btn')
        self.volume_btn.setObjectName('volume_btn')
        self.download_btn.setObjectName('download_btn')
        self.toggle_video_btn.setObjectName('toggle_video_btn')
        self.toggle_pip_btn.setObjectName('toggle_pip_btn')

        self.progress_slider = ProgressSlider(app=app, parent=self)

        self.volume_btn.setToolTip('调整音量')
        self.playlist_btn.setToolTip('显示当前播放列表')
        self.download_btn.setToolTip('下载歌曲（未实现，欢迎 PR）')
        self.download_btn.setCheckable(True)

        self.song_title_label = LineSongLabel(self._app)
        self.song_title_label.setAlignment(Qt.AlignCenter)
        self.song_source_label = SourceLabel(self._app, parent=self)

        self.cover_label = CoverLabelV2(app)
        self.duration_label = DurationLabel(app, parent=self)
        self.position_label = ProgressLabel(app, parent=self)

        # we should enable focus since we want to have shortcut keys
        self.setFocusPolicy(Qt.StrongFocus)
        self.song_source_label.setObjectName('song_source_label')

        self.volume_btn.change_volume_needed.connect(
            lambda volume: setattr(self._app.player, 'volume', volume))

        player = self._app.player
        player.metadata_changed.connect(self.on_metadata_changed, aioqueue=True)
        player.volume_changed.connect(self.volume_btn.on_volume_changed)

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
        self.download_btn.setFixedSize(15, 15)
        self.download_btn.hide()
        self.mv_btn.setFixedHeight(16)
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
        self._layout.addWidget(self.media_btns)
        self._layout.addSpacing(26)
        self._layout.addWidget(self.volume_btn)
        # 18 = 200(left_panel_width) - 4 * 30(btn) - 20 - 8 - 8 -26
        self._layout.addSpacing(50)
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
        self._layout.addSpacing(50)
        self._layout.addWidget(self.playlist_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.toggle_video_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.toggle_pip_btn)
        self._layout.addSpacing(18)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def on_metadata_changed(self, metadata):
        if not metadata:
            self.song_source_label.setText('歌曲来源')
            return

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

        released = metadata.get('released', '')
        if released:
            self.cover_label.setToolTip(f'专辑发行日期：{released}')
        else:
            self.cover_label.setToolTip('')
        # Set song artwork.
        artwork = metadata.get('artwork', '')
        artwork_uid = metadata.get('uri', artwork)
        if artwork:
            aio.run_afn(self.cover_label.show_cover, artwork, artwork_uid)
            aio.run_afn(self._app.ui.floating_box.show_cover, artwork, artwork_uid)
            aio.run_afn(self._app.ui.floating_box.show_cover, artwork, artwork_uid)

        # Set audio bitrate info if available.
        media = self._app.player.current_media
        if media is not None and media.type_ == MediaType.audio:
            props = media.props
            if props.bitrate:
                text = self.song_source_label.text()
                self.song_source_label.setText(f'{text} - {props.bitrate}kbps')


class TopPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.pc_panel = PlayerControlPanel(self._app, self)
        self.setObjectName('top_panel')

        self.setFixedHeight(60)

        self._layout.addWidget(self.pc_panel)
