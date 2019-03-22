import asyncio
import logging
from PyQt5.QtCore import Qt, QTime, pyqtSignal
from PyQt5.QtGui import QKeySequence, QFontMetrics
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
    QVBoxLayout,
)

from fuocore.player import PlaybackMode, State
from fuocore.utils import parse_ms

from feeluown.widgets.separator import Separator
from feeluown.widgets.playlists import PlaylistsView
from feeluown.widgets.provider import ProvidersView
from feeluown.widgets.collections import CollectionsView
from feeluown.widgets.my_music import MyMusicView
from feeluown.widgets.volume_button import VolumeButton
from feeluown.widgets.statusline import StatusLine, StatusLineItem
from feeluown.widgets.magicbox import MagicBox
from feeluown.widgets.table_container import SongsTableContainer
from feeluown.widgets.statusline_items import PluginStatus
from feeluown.widgets.mpv_widget import MpvOpenGLWidget

from .helpers import use_mac_theme, async_run

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

        self.next_btn.clicked.connect(self._app.player.play_next)
        self.previous_btn.clicked.connect(self._app.player.play_previous)
        self.pp_btn.clicked.connect(self._app.player.toggle)
        self.pms_btn.clicked.connect(self._switch_playback_mode)

        self._app.player.state_changed.connect(self._on_player_state_changed)
        self._app.player.position_changed.connect(self.on_position_changed)
        self._app.player.duration_changed.connect(self.on_duration_changed)
        self._app.player.playlist.playback_mode_changed.connect(
            self.on_playback_mode_changed)
        self._app.player.playlist.song_changed.connect(
            self.on_player_song_changed, aioqueue=True)
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
        elided_text = font_metrics.elidedText(
            text, Qt.ElideRight, self.progress_slider.width() - 100)
        self.song_source_label.setText(source_name_map[song.source])
        self.song_title_label.setText(elided_text)
        loop = asyncio.get_event_loop()
        loop.create_task(self.update_mv_btn_status(song))

    async def update_mv_btn_status(self, song):
        mv = await async_run(lambda: song.mv)
        if mv:
            self.mv_btn.setToolTip(mv.name)
            self.mv_btn.setEnabled(True)
        else:
            self.mv_btn.setEnabled(False)

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


class BottomPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)

        self.back_btn = QPushButton('⇦', self)
        self.forward_btn = QPushButton('⇨', self)
        self.magicbox = MagicBox(self._app)
        self.status_line = StatusLine(self._app)
        self.back_btn.setObjectName('back_btn')
        self.forward_btn.setObjectName('forward_btn')
        self.setObjectName('bottom_panel')

        self.plugin_status_line_item = StatusLineItem(
            'plugin',
            PluginStatus(self._app))
        self.status_line.add_item(self.plugin_status_line_item)

        self._layout.addWidget(self.back_btn)
        self._layout.addWidget(self.forward_btn)
        self._layout.addWidget(self.magicbox)
        self._layout.addWidget(self.status_line)

        height = self.magicbox.height()
        self.setFixedHeight(height)
        self.back_btn.setFixedWidth(height)
        self.forward_btn.setFixedWidth(height)

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.back_btn.setEnabled(False)
        self.forward_btn.setEnabled(False)
        self.back_btn.clicked.connect(self._app.browser.back)
        self.forward_btn.clicked.connect(self._app.browser.forward)


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
            '手动编辑 fuo 文件即可编辑收藏集中的音乐资源，也可以在界面上拖拽来增删歌曲。'
        )
        self.playlists_header = QLabel('歌单列表', self)
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
        self.my_music_view = MyMusicView(self)
        self.collections_view = CollectionsView(self)

        self.providers_con = Container(self.library_header, self.providers_view)
        self.collections_con = Container(self.collections_header, self.collections_view)
        self.playlists_con = Container(self.playlists_header, self.playlists_view)
        self.my_music_con = Container(self.my_music_header, self.my_music_view)

        self.providers_view.setModel(self._app.pvd_uimgr.model)
        self.playlists_view.setModel(self._app.pl_uimgr.model)
        self.my_music_view.setModel(self._app.mymusic_uimgr.model)
        self.collections_view.setModel(self._app.coll_uimgr.model)

        self._layout = QVBoxLayout(self)

        if use_mac_theme():
            self._layout.setSpacing(0)
            self._layout.setContentsMargins(6, 4, 0, 0)
        self._layout.addWidget(self.providers_con)
        self._layout.addWidget(self.collections_con)
        self._layout.addWidget(self.my_music_con)
        self._layout.addWidget(self.playlists_con)
        self._layout.addStretch(0)

        self.providers_view.setFrameShape(QFrame.NoFrame)
        self.playlists_view.setFrameShape(QFrame.NoFrame)
        self.my_music_view.setFrameShape(QFrame.NoFrame)
        self.collections_view.setFrameShape(QFrame.NoFrame)
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumWidth(180)
        self.setMaximumWidth(250)
        # 让各个音乐库来决定是否显示这些组件
        self.playlists_con.hide()
        self.my_music_con.hide()

        self.playlists_view.show_playlist.connect(
            lambda pl: self._app.browser.goto(model=pl))
        self._app.browser.route('/colls/<identifier>')(self.__handle_show_coll)
        self.collections_view.show_collection.connect(self.show_coll)

    def show_coll(self, coll):
        coll_id = self._app.coll_uimgr.get_coll_id(coll)
        self._app.browser.goto(uri='/colls/{}'.format(coll_id))

    def __handle_show_coll(self, req, identifier):
        coll = self._app.coll_uimgr.get(int(identifier))
        self._app.ui.table_container.show_collection(coll)


class RightPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.table_container = SongsTableContainer(self._app, self)
        self._layout.addWidget(self.table_container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)


class Ui:

    def __init__(self, app):
        self._app = app
        self._layout = QVBoxLayout(app)
        self._top_separator = Separator(parent=app)
        self._bottom_separator = Separator(parent=app)
        self._splitter = QSplitter(app)
        if use_mac_theme():
            self._splitter.setHandleWidth(0)

        # NOTE: 以位置命名的部件应该只用来组织界面布局，不要
        # 给其添加任何功能性的函数
        self.top_panel = TopPanel(app, app)
        self.bottom_panel = BottomPanel(app, app)
        self._left_panel_container = QScrollArea(app)
        self._left_panel_container.setWidgetResizable(True)
        self._left_panel_container.setFrameShape(QFrame.NoFrame)
        self.left_panel = LeftPanel(self._app, self._left_panel_container)
        self._left_panel_container.setWidget(self.left_panel)
        self.right_panel = RightPanel(self._app, self._splitter)
        self.mpv_widget = MpvOpenGLWidget(self._app)
        self.mpv_widget.hide()

        # alias
        self.magicbox = self.bottom_panel.magicbox
        self.pc_panel = self.top_panel.pc_panel
        self.table_container = self.right_panel.table_container
        self.songs_table = self.right_panel.table_container
        self.back_btn = self.bottom_panel.back_btn
        self.forward_btn = self.bottom_panel.forward_btn
        self.toggle_video_btn = self.pc_panel.toggle_video_btn

        # 对部件进行一些 UI 层面的初始化
        self._splitter.addWidget(self._left_panel_container)
        self._splitter.addWidget(self.right_panel)

        self.right_panel.setMinimumWidth(780)
        self._left_panel_container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._layout.addWidget(self.bottom_panel)
        self._layout.addWidget(self._bottom_separator)
        self._layout.addWidget(self._splitter)
        self._layout.addWidget(self.mpv_widget)
        self._layout.addWidget(self._top_separator)
        self._layout.addWidget(self.top_panel)

        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.top_panel.layout().setSpacing(0)
        self.top_panel.layout().setContentsMargins(0, 0, 0, 0)

        self.pc_panel.playlist_btn.clicked.connect(self.show_player_playlist)
        self.pc_panel.mv_btn.clicked.connect(self._play_mv)
        self.toggle_video_btn.clicked.connect(self._toggle_video_widget)
        self._app.player.video_format_changed.connect(
            self.on_video_format_changed)

        self._app.hotkey_mgr.registe(
            [QKeySequence('Ctrl+F'), QKeySequence(':'), QKeySequence('Alt+x')],
            self.magicbox.setFocus
        )

    def _play_mv(self):
        song = self._app.player.current_song
        url = song.mv.media.url_ahap
        self._app.player.play(url)
        self.show_video_widget()

    def show_player_playlist(self):
        songs = self._app.playlist.list()
        self.table_container.show_player_playlist(songs)

    def on_video_format_changed(self, vformat):
        if vformat is None:
            self.hide_video_widget()
            self.toggle_video_btn.hide()
        else:
            self.toggle_video_btn.show()

    def _toggle_video_widget(self):
        if self.mpv_widget.isVisible():
            self.hide_video_widget()
        else:
            self.show_video_widget()

    def hide_video_widget(self):
        self.mpv_widget.hide()
        self._splitter.show()
        self.bottom_panel.show()
        self._bottom_separator.show()
        self.pc_panel.toggle_video_btn.setText('△')

    def show_video_widget(self):
        self.bottom_panel.hide()
        self._bottom_separator.hide()
        self._splitter.hide()
        self.mpv_widget.show()
        self.pc_panel.toggle_video_btn.setText('▽')
