import asyncio
import logging

from PyQt5.QtCore import Qt, QTime, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QFontMetrics, QPainter, QFont, QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from feeluown import __upgrade_desc__
from feeluown.components.searchbox import SearchBox
from feeluown.components.separator import Separator
from feeluown.components.playlists import (
    PlaylistsView,
    PlaylistsModel,
)
from feeluown.components.library import LibrariesView
from feeluown.components.history import HistoriesView
from feeluown.containers.table_container import SongsTableContainer

from .consts import PlaybackMode
from .utils import parse_ms


logger = logging.getLogger(__name__)


class VolumeSlider(QSlider):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setOrientation(Qt.Horizontal)
        #self.setRange(0, 100)   # player volume range
        #self.setValue(100)
        self.setToolTip('调教播放器音量')


class ProgressSlider(QSlider):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setOrientation(Qt.Horizontal)

    def set_duration(self, ms):
        self.setRange(0, ms / 1000)

    def update_state(self, ms):
        self.setValue(ms / 1000)


class PlayerControlPanel(QFrame):

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        class Button(QPushButton):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                # self.setFixedSize(40, 40)

        # initialize sub widgets
        self._layout = QHBoxLayout(self)
        self.previous_btn = Button(self)
        self.pp_btn = Button(self)
        self.next_btn = Button(self)
        self.pms_btn = Button(self)
        self.volume_btn = Button(self)

        self.pms_btn.setToolTip('该功能尚未开发完成，欢迎 PR')
        self.volume_btn.setToolTip('该功能尚未开发完成，欢迎 PR')

        self.previous_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.pp_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.next_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.volume_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))

        self.song_title_label = QLabel('No song is playing.', parent=self)
        self.song_title_label.setAlignment(Qt.AlignCenter)
        self.duration_label = QLabel('00:00', parent=self)
        self.position_label = QLabel('00:00', parent=self)
        self.progress_slider = ProgressSlider(self)

        self.next_btn.clicked.connect(self._app.player.playlist.play_next)
        self.previous_btn.clicked.connect(self._app.player.playlist.play_previous)
        self.pp_btn.clicked.connect(self._app.player.toggle)

        # set widget layout
        self.progress_slider.setMinimumWidth(480)
        self.progress_slider.setMaximumWidth(600)
        self.progress_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._sub_layout = QVBoxLayout(self)
        self._sub_layout.addWidget(self.song_title_label)
        self._sub_layout.addWidget(self.progress_slider)

        self._layout.addSpacing(10)
        self._layout.addWidget(self.previous_btn)
        self._layout.addWidget(self.pp_btn)
        self._layout.addWidget(self.next_btn)
        self._layout.addSpacing(15)
        self._layout.addStretch(0)
        self._layout.addWidget(self.position_label)
        self._layout.addSpacing(7)
        self._layout.addLayout(self._sub_layout)
        self._layout.addSpacing(7)
        self._layout.addWidget(self.duration_label)
        self._layout.addSpacing(5)
        self._layout.addStretch(0)
        self._layout.addWidget(self.pms_btn)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.volume_btn)
        self._layout.addSpacing(10)

        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def on_duration_changed(self, duration):
        m, s = parse_ms(duration)
        t = QTime(0, m, s)
        self.duration_label.setText(t.toString('mm:ss'))

    def on_position_changed(self, position):
        m, s = parse_ms(position)
        t = QTime(0, m, s)
        self.position_label.setText(t.toString('mm:ss'))

    def on_playback_mode_changed(self, playback_mode):
        self.pms_btn.setText(playback_mode.value)

    def on_player_song_changed(self, song):
        self.song_title_label.setText(
            '♪  {title} - {artists_name}'.format(
                title=song.title,
                artists_name=song.artists_name))


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

        self.library_header = QLabel('我的音乐', self)
        self.playlists_header = QLabel('歌单列表', self)
        self.history_header = QLabel('历史记录', self)

        self.playlists_view = PlaylistsView(self)
        self.libraries_view = LibrariesView(self)
        self.histories_view = HistoriesView(self)
        self._splitter = QSplitter(Qt.Vertical, self)

        self.libraries_view.setModel(self._app.libraries)
        self.histories_view.setModel(self._app.histories)

        self._layout = QVBoxLayout(self)
        self._splitter.addWidget(self.library_header)
        self._splitter.addWidget(self.libraries_view)
        self._splitter.addWidget(self.history_header)
        self._splitter.addWidget(self.histories_view)
        self._splitter.addWidget(self.playlists_header)
        self._splitter.addWidget(self.playlists_view)
        self._layout.addWidget(self._splitter)

        self.libraries_view.setFrameShape(QFrame.NoFrame)
        self.playlists_view.setFrameShape(QFrame.NoFrame)
        self.histories_view.setFrameShape(QFrame.NoFrame)
        self.setMinimumWidth(180)
        self.setMaximumWidth(250)

        self.playlists_view.show_playlist.connect(
            lambda pl: asyncio.ensure_future(self.show_model(pl)))
        self.histories_view.show_model.connect(
            lambda model: asyncio.ensure_future(self.show_model(model)))

    def set_playlists(self, playlists):
        model = PlaylistsModel(playlists, self)
        self.playlists_view.setModel(model)

    async def show_model(self, playlist):
        await self._app.ui.songs_table_container.show_model(playlist)


class RightPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.widget = None
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)
        self.setObjectName('right_panel')

    def set_widget(self, widget):
        if self.widget and self.widget != widget:
            self._layout.removeWidget(self.widget)
            self.widget.hide()
            widget.show()
            self._layout.addWidget(widget)
        else:
            self._layout.addWidget(widget)
        self.widget = widget


class SongLabel(QLabel):
    def __init__(self, text=None, parent=None):
        super().__init__(text, parent)
        self.set_song('No song is playing')

    def set_song(self, song_text):
        self.setText('♪  ' + song_text + ' ')


class ThemeCombo(QComboBox):
    clicked = pyqtSignal()
    signal_change_theme = pyqtSignal([str])

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setObjectName('theme_switch_btn')
        self.setEditable(False)
        self.maximum_width = 150
        #self.set_theme_style()
        self.setFrame(False)
        self.current_theme = self._app.theme_manager.current_theme.name
        self.themes = [self.current_theme]
        self.set_themes(self.themes)

        self.currentIndexChanged.connect(self.on_index_changed)

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
                border: 0px;
                padding: 0px 4px;
                border-radius: 0px;
            }}
            #{0}::drop-down {{
                width: 0px;
                border: 0px;
            }}
            #{0} QAbstractItemView {{
                border: 0px;
                min-width: 200px;
            }}
        '''.format(self.objectName(),
                   theme.color4.name(),
                   theme.background.name(),
                   theme.foreground.name())
        self.setStyleSheet(style_str)

    @pyqtSlot(int)
    def on_index_changed(self, index):
        if index < 0 or not self.themes:
            return
        metrics = QFontMetrics(self.font())
        if self.themes[index] == self.current_theme:
            return
        self.current_theme = self.themes[index]
        name = '❀ ' + self.themes[index]
        width = metrics.width(name)
        if width < self.maximum_width:
            self.setFixedWidth(width + 10)
            self.setItemText(index, name)
            self.setToolTip(name)
        else:
            self.setFixedWidth(self.maximum_width)
            text = metrics.elidedText(name, Qt.ElideRight,
                                      self.width())
            self.setItemText(index, text)
            self.setToolTip(text)
        self.signal_change_theme.emit(self.current_theme)

    def add_item(self, text):
        self.addItem('❀ ' + text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and \
                self.rect().contains(event.pos()):
            self.clicked.emit()
            self.showPopup()

    def set_themes(self, themes):
        self.clear()
        if self.current_theme:
            self.themes = [self.current_theme]
            self.add_item(self.current_theme)
        else:
            self.themes = []
        for theme in themes:
            if theme not in self.themes:
                self.add_item(theme)
                self.themes.append(theme)


class PlayerStateLabel(QLabel):
    def __init__(self, app, text=None, parent=None):
        super().__init__('♫', parent)
        self._app = app

        self.setObjectName('player_state_label')
        self.setToolTip('这里显示的是播放器的状态\n'
                        'Buffered 代表该音乐已经可以开始播放\n'
                        'Stalled 表示正在加载或者由于某种原因而被迫中断\n'
                        'Loading 代表正在加载该音乐\n'
                        'Loaded 代表改歌曲是本地歌曲，并加载完毕\n'
                        'Failed 代表加载音乐失败\n'
                        '这里的进度条代表加载音乐的进度')
        #self.set_theme_style()
        self._progress = 100
        self._show_progress = False

    def paintEvent(self, event):
        if self._show_progress:
            painter = QPainter(self)
            p_bg_color = self._app.theme_manager.current_theme.color0
            painter.fillRect(self.rect(), p_bg_color)
            bg_color = self._app.theme_manager.current_theme.color6_light
            rect = self.rect()
            percent = self._progress * 1.0 / 100
            rect.setWidth(int(rect.width() * percent))
            painter.fillRect(rect, bg_color)
            painter.drawText(self.rect(), Qt.AlignVCenter | Qt.AlignHCenter,
                             'buffering' + str(self._progress) + '%')
            self._show_progress = False
        else:
            super().paintEvent(event)

    def show_progress(self, progress):
        self._progress = progress
        self._show_progress = True
        if self._progress == 100:
            self._show_progress = False
        self.update()

    def set_text(self, text):
        self.setText(('♫ ' + text).upper())

    @property
    def common_style(self):
        style_str = '''
            #{0} {{
                padding-left: 3px;
                padding-right: 5px;
            }}
        '''.format(self.objectName())
        return style_str

    def set_theme_style(self):
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

    def set_error_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.color1_light.name(),
                   theme.color7.name())
        self.setStyleSheet(style_str + self.common_style)

    def set_normal_style(self):
        #self.set_theme_style()
        pass


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


class AppStatusLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setText('♨ Normal'.upper())
        self.setToolTip('点击可以切换到其他模式哦 ~\n'
                        '不过暂时还没实现这个功能...敬请期待 ~\n' +
                        '此版本更新摘要:\n' +
                        __upgrade_desc__)
        self.setObjectName('app_status_label')

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and \
                self.rect().contains(event.pos()):
            self.clicked.emit()


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


class StatusPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.player_state_label = PlayerStateLabel(self._app)
        self.app_status_label = AppStatusLabel(self._app)
        self.network_status_label = NetworkStatus(self._app)
        self.message_label = MessageLabel(self._app)
        self.theme_switch_btn = ThemeCombo(self._app, self)

        self.setup_ui()
        self.setObjectName('status_panel')
        #self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
            }}
        '''.format(self.objectName(),
                   theme.color0.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self.setFixedHeight(18)
        self._layout.addWidget(self.player_state_label)
        self._layout.addWidget(self.app_status_label)
        self._layout.addWidget(self.network_status_label)
        self._layout.addStretch(0)
        self._layout.addWidget(self.message_label)
        self._layout.addStretch(0)
        self._layout.addWidget(self.theme_switch_btn)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)


class LyricFrame(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app


class Ui(object):
    def __init__(self, app):
        self._app = app
        self._layout = QVBoxLayout(app)
        self._bottom_layout = QHBoxLayout(app)
        self._top_separator = Separator(app)
        self._splitter = QSplitter(app)

        # NOTE: 以位置命名的部件应该只用来组织界面布局，不要
        # 给其添加任何功能性的函数
        self.top_panel = TopPanel(app, app)
        self.left_panel = LeftPanel(self._app, self._splitter)
        self.right_panel = RightPanel(self._app, self._splitter)

        self.pc_panel = self.top_panel.pc_panel
        self.searchbox = SearchBox(self._app)
        self.status_panel = StatusPanel(app, app)
        self.songs_table_container = SongsTableContainer(self._app, self.right_panel)

        # 对部件进行一些 UI 层面的初始化
        self._splitter.addWidget(self.left_panel)
        self._splitter.addWidget(self.right_panel)
        self.right_panel.set_widget(self.songs_table_container)
        self.searchbox.setFrame(False)
        self.status_panel.hide()

        self.right_panel.setMinimumWidth(780)
        self.left_panel.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._layout.addWidget(self.top_panel)
        self._layout.addWidget(self._top_separator)
        self._layout.addWidget(self._splitter)
        self._layout.addWidget(self.status_panel)
        self._layout.addWidget(self.searchbox)
        # self._layout.addLayout(self._bottom_layout)
        # self._bottom_layout.addWidget(self.searchbox)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.top_panel.layout().setSpacing(0)
        self.top_panel.layout().setContentsMargins(0, 0, 0, 0)

        self.searchbox.textChanged.connect(self.songs_table_container.search)
        self.searchbox.returnPressed.connect(self.search_library)

        self._app.hotkey_manager.registe(
            [QKeySequence('Ctrl+F'), QKeySequence(':'), QKeySequence('Alt+x')],
            self.searchbox.setFocus
        )

    def search_library(self):
        text = self.searchbox.text()
        songs = self._app.provider_manager.search(text)
        self.songs_table_container.show_songs(songs)
