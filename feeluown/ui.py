import asyncio
import logging
from PyQt5.QtCore import Qt, QTime, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QKeySequence, QFontMetrics
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QStyle,
    QVBoxLayout,
)

from fuocore.player import PlaybackMode, State

from feeluown.components.separator import Separator
from feeluown.components.playlists import PlaylistsView
from feeluown.components.provider import ProvidersView
from feeluown.components.history import HistoriesView
from feeluown.components.collections import CollectionsView
from feeluown.components.my_music import MyMusicView
from feeluown.components.volume_button import VolumeButton
from feeluown.containers.magicbox import MagicBox
from feeluown.containers.table_container import SongsTableContainer

from .helpers import use_mac_theme
from .utils import parse_ms

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
                # 按钮文字一般是一个 symbol，长度控制为 40 是满足需求的
                self.setMaximumWidth(40)

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
        self.volume_btn.change_volume_needed.connect(
            lambda volume: setattr(self._app.player, 'volume', volume))
        self.playlist_btn = IconButton(parent=self)

        #: mark song as favorite button
        self.like_btn = QPushButton(self)
        self.mv_btn = QPushButton('MV', self)
        self.download_btn = QPushButton(self)

        self.previous_btn.setObjectName('previous_btn')
        self.pp_btn.setObjectName('pp_btn')
        self.next_btn.setObjectName('next_btn')
        self.playlist_btn.setObjectName('playlist_btn')
        self.volume_btn.setObjectName('volume_btn')
        self.pms_btn.setObjectName('pms_btn')
        self.download_btn.setObjectName('download_btn')
        self.like_btn.setObjectName('like_btn')
        self.mv_btn.setObjectName('mv_btn')

        self.progress_slider = ProgressSlider(self)

        self.pms_btn.setToolTip('修改播放模式')
        self.volume_btn.setToolTip('调整音量')
        self.playlist_btn.setToolTip('显示当前播放列表')
        self.progress_slider.setToolTip('拖动调节进度')

        # TODO: implementation
        self.mv_btn.setToolTip('播放 MV（未实现，欢迎 PR）')
        self.download_btn.setToolTip('下载歌曲（未实现，欢迎 PR）')
        self.like_btn.setToolTip('收藏歌曲（未实现，欢迎 PR）')

        if not use_mac_theme():
            self.previous_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
            self.pp_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.next_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
            self.volume_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
            self.playlist_btn.setText('🎶')
        else:
            self.pp_btn.setCheckable(True)
            self.like_btn.setCheckable(True)
            self.download_btn.setCheckable(True)

        self.song_title_label = QLabel('No song is playing.', parent=self)
        self.song_source_label = QLabel('歌曲来源', parent=self)
        self.song_title_label.setAlignment(Qt.AlignCenter)
        self.duration_label = QLabel('00:00', parent=self)
        self.position_label = QLabel('00:00', parent=self)

        self.song_source_label.setObjectName('song_source_label')

        self.next_btn.clicked.connect(self._app.player.play_next)
        self.previous_btn.clicked.connect(self._app.player.play_previous)
        self.pp_btn.clicked.connect(self._app.player.toggle)
        self.pms_btn.clicked.connect(self._switch_playback_mode)

        self._app.player.state_changed.connect(self._on_player_state_changed)
        self._app.player.playlist.playback_mode_changed.connect(
            self.on_playback_mode_changed)
        self._app.player.playlist.song_changed.connect(
            self.on_player_song_changed)
        self.progress_slider.resume_player_needed.connect(self._app.player.resume)
        self.progress_slider.pause_player_needed.connect(self._app.player.pause)
        self.progress_slider.change_position_needed.connect(
            lambda value: setattr(self._app.player, 'position', value))

        self._update_pms_btn_text()
        self._setup_ui()

    def _setup_ui(self):
        # set widget layout
        self.progress_slider.setMinimumWidth(480)
        self.progress_slider.setMaximumWidth(600)
        self.song_source_label.setFixedHeight(20)
        self.progress_slider.setFixedHeight(20)  # half of parent height
        self.position_label.setFixedWidth(45)
        self.duration_label.setFixedWidth(45)
        self.like_btn.setFixedSize(15, 15)
        self.download_btn.setFixedSize(15, 15)
        self.mv_btn.setFixedHeight(16)

        self.progress_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._sub_layout = QVBoxLayout()
        self._sub_top_layout = QHBoxLayout()

        # add space to make top layout align with progress slider
        self._sub_top_layout.addSpacing(3)
        self._sub_top_layout.addWidget(self.song_source_label)
        self._sub_top_layout.addSpacing(5)
        self._sub_top_layout.addWidget(self.song_title_label)
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
        self._layout.addStretch(0)
        self._layout.addWidget(self.position_label)
        self._layout.addSpacing(7)
        self._layout.addLayout(self._sub_layout)
        self._layout.addSpacing(7)
        self._layout.addWidget(self.duration_label)
        self._layout.addSpacing(5)
        self._layout.addStretch(0)
        self._layout.addWidget(self.pms_btn)
        self._layout.addSpacing(8)
        self._layout.addWidget(self.playlist_btn)
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
        m, s = parse_ms(duration)
        t = QTime(0, m, s)
        self.duration_label.setText(t.toString('mm:ss'))

    def on_position_changed(self, position):
        m, s = parse_ms(position)
        t = QTime(0, m, s)
        self.position_label.setText(t.toString('mm:ss'))

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
        text = '{} - {}'.format(song.title, song.artists_name)
        elided_text = font_metrics.elidedText(
            text, Qt.ElideRight, self.progress_slider.width() - 100)
        self.song_source_label.setText(source_name_map[song.source])
        self.song_title_label.setText(elided_text)

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


class LeftPanel(QFrame):

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.library_header = QLabel('音乐库', self)
        self.collections_header = QLabel('本地收藏 (Beta)', self)
        self.collections_header.setToolTip(
            '我们可以在本地建立『收藏集』来收藏自己喜欢的音乐资源\n\n'
            '每个收藏集都以一个独立 .fuo 文件的存在，'
            '将鼠标悬浮在收藏集上，可以查看文件所在路径。\n'
            '新建 fuo 文件，则可以新建收藏集，文件名即是收藏集的名字。\n\n'
            '手动编辑 fuo 文件即可编辑收藏集中的音乐资源，'
            '以后有时间会添加通过 GUI 拖拽来实现快速收藏的功能，也欢迎 PR。'
        )
        self.playlists_header = QLabel('歌单列表', self)
        self.history_header = QLabel('浏览历史记录', self)
        self.my_music_header = QLabel('我的音乐', self)

        class Container(QFrame):
            def __init__(self, label, view, parent=None):
                super().__init__(parent)

                self._layout = QVBoxLayout(self)
                self._layout.setContentsMargins(0, 0, 0, 0)
                self._layout.setSpacing(0)
                label.setFixedHeight(25)
                self._layout.addWidget(label)
                self._layout.addWidget(view)
                self._layout.addStretch(0)
                # XXX: 本意是让 Container 下方不要出现多余的空间
                self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)


        self.playlists_view = PlaylistsView(self)
        self.providers_view = ProvidersView(self)
        self.histories_view = HistoriesView(self)
        self.my_music_view = MyMusicView(self)
        self.collections_view = CollectionsView(self)

        self.providers_con = Container(self.library_header, self.providers_view)
        self.collections_con = Container(self.collections_header, self.collections_view)
        self.histories_con = Container(self.history_header, self.histories_view)
        self.playlists_con = Container(self.playlists_header, self.playlists_view)
        self.my_music_con = Container(self.my_music_header, self.my_music_view)

        self.providers_view.setModel(self._app.providers)
        self.histories_view.setModel(self._app.histories)
        self.playlists_view.setModel(self._app.playlists)
        self.my_music_view.setModel(self._app.my_music)
        self.collections_view.setModel(self._app.collections)

        self._layout = QVBoxLayout(self)

        if use_mac_theme():
            self._layout.setSpacing(0)
            self._layout.setContentsMargins(6, 4, 0, 0)
        self._layout.addWidget(self.providers_con)
        self._layout.addWidget(self.collections_con)
        self._layout.addWidget(self.my_music_con)
        self._layout.addWidget(self.histories_con)
        self._layout.addWidget(self.playlists_con)
        self._layout.addStretch(0)

        self.providers_view.setFrameShape(QFrame.NoFrame)
        self.playlists_view.setFrameShape(QFrame.NoFrame)
        self.histories_view.setFrameShape(QFrame.NoFrame)
        self.my_music_view.setFrameShape(QFrame.NoFrame)
        self.collections_view.setFrameShape(QFrame.NoFrame)
        self.setMinimumWidth(180)
        self.setMaximumWidth(250)

        self.playlists_view.show_playlist.connect(
            lambda pl: asyncio.ensure_future(self.show_model(pl)))
        self.histories_view.show_model.connect(
            lambda model: asyncio.ensure_future(self.show_model(model)))
        self.collections_view.show_collection.connect(
            lambda collection: self._app.ui.table_container.show_collection(collection))

        # 让各个音乐库来决定是否显示这些组件
        self.playlists_con.hide()
        self.my_music_con.hide()

        # 历史记录暂时隐藏
        self.histories_con.hide()

    async def show_model(self, model):
        await self._app.ui.table_container.show_model(model)


class RightPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.table_container = SongsTableContainer(self._app, self)
        self._layout.addWidget(self.table_container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)


class MessageLabel(QLabel):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setObjectName('message_label')
        self._interval = 3
        self.timer = QTimer()
        self.queue = []
        self.hide()

        self.timer.timeout.connect(self.access_message_queue)

    @property
    def common_style(self):
        style_str = '''
            #{0} {{
                padding-left: 3px;
                padding-right: 5px;
            }}
        '''.format(self.objectName())
        return style_str

    def _set_error_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.color1_light.name(),
                   theme.color7_light.name())
        self.setStyleSheet(style_str + self.common_style)

    def _set_normal_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.color6_light.name(),
                   theme.color7.name())
        self.setStyleSheet(style_str + self.common_style)

    def show_message(self, text, error=False):
        if self.isVisible():
            self.queue.append({'error': error, 'message': text})
            self._interval = 1.5
            return
        if error:
            self._set_error_style()
        else:
            self._set_normal_style()
        self.setText(str(len(self.queue)) + ': ' + text)
        self.show()
        self.timer.start(self._interval * 1000)

    def access_message_queue(self):
        self.hide()
        if self.queue:
            m = self.queue.pop(0)
            self.show_message(m['message'], m['error'])
        else:
            self._interval = 3


class NetworkStatus(QLabel):
    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setToolTip('这里显示的是当前网络状态')
        self.setObjectName('network_status_label')
        self._progress = 100
        self._show_progress = False

        self.set_state(1)

    def paintEvent(self, event):
        if self._show_progress:
            painter = QPainter(self)
            p_bg_color = self._app.theme_manager.current_theme.color0
            painter.fillRect(self.rect(), p_bg_color)
            bg_color = self._app.theme_manager.current_theme.color3
            rect = self.rect()
            percent = self._progress * 1.0 / 100
            rect.setWidth(int(rect.width() * percent))
            painter.fillRect(rect, bg_color)
            painter.drawText(self.rect(), Qt.AlignVCenter | Qt.AlignHCenter,
                             str(self._progress) + '%')
            self._show_progress = False
        else:
            super().paintEvent(event)

    @property
    def common_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
                padding-left: 5px;
                padding-right: 5px;
                font-size: 14px;
                font-weight: bold;
            }}
        '''.format(self.objectName(),
                   theme.color3.name(),
                   theme.background.name())
        return style_str

    def set_theme_style(self):
        self.setStyleSheet(self.common_style)

    def _set_error_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
            }}
        '''.format(self.objectName(),
                   theme.color5.name())
        self.setStyleSheet(self.common_style + style_str)

    def _set_normal_style(self):
        self.setStyleSheet(self.common_style)

    def set_state(self, state):
        if state == 0:
            self._set_error_style()
            self.setText('✕')
        elif state == 1:
            self._set_normal_style()
            self.setText('✓')

    def show_progress(self, progress):
        self._progress = progress
        self._show_progress = True
        if self._progress == 100:
            self._show_progress = False
        self.update()


class Ui:
    def __init__(self, app):
        self._app = app
        self._layout = QVBoxLayout(app)
        self._bottom_layout = QHBoxLayout()
        self._top_separator = Separator(parent=app)
        self._splitter = QSplitter(app)
        if use_mac_theme():
            self._splitter.setHandleWidth(0)

        # NOTE: 以位置命名的部件应该只用来组织界面布局，不要
        # 给其添加任何功能性的函数
        self.top_panel = TopPanel(app, app)
        self._left_panel_container = QScrollArea(self._app)
        self._left_panel_container.setWidgetResizable(True)
        self.left_panel = LeftPanel(self._app, self._splitter)
        self._left_panel_container.setWidget(self.left_panel)
        self.right_panel = RightPanel(self._app, self._splitter)

        # alias
        self.pc_panel = self.top_panel.pc_panel
        self.table_container = self.right_panel.table_container
        self.magicbox = MagicBox(self._app)

        # 对部件进行一些 UI 层面的初始化
        self._splitter.addWidget(self._left_panel_container)
        self._splitter.addWidget(self.right_panel)

        self.right_panel.setMinimumWidth(780)
        self._left_panel_container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if use_mac_theme():
            self._layout.addWidget(self.magicbox)
            self._layout.addWidget(self._splitter)
            self._layout.addWidget(self._top_separator)
            self._layout.addWidget(self.top_panel)
        else:
            self._layout.addWidget(self.top_panel)
            self._layout.addWidget(self._top_separator)
            self._layout.addWidget(self._splitter)
            self._layout.addWidget(self.magicbox)

        # self._layout.addLayout(self._bottom_layout)
        # self._bottom_layout.addWidget(self.magicbox)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.top_panel.layout().setSpacing(0)
        self.top_panel.layout().setContentsMargins(0, 0, 0, 0)

        self.pc_panel.playlist_btn.clicked.connect(self.show_player_playlist)

        self._app.hotkey_manager.registe(
            [QKeySequence('Ctrl+F'), QKeySequence(':'), QKeySequence('Alt+x')],
            self.magicbox.setFocus
        )

    def show_player_playlist(self):
        songs = self._app.playlist.list()
        self.table_container.show_player_playlist(songs)
