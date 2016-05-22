import asyncio
import logging

from PyQt5.QtGui import QFontMetrics, QPainter
from PyQt5.QtCore import Qt, QTime, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QMenu, QAction
from PyQt5.QtMultimedia import QMediaPlayer

from feeluown.libs.widgets.base import FFrame, FButton, FLabel, FScrollArea,\
    FComboBox
from feeluown.libs.widgets.labels import _BasicLabel
from feeluown.libs.widgets.sliders import _BasicSlider
from feeluown.libs.widgets.components import LP_GroupHeader, LP_GroupItem, \
    MusicTable

from .utils import parse_ms
from .consts import PlaybackMode


logger = logging.getLogger(__name__)


class PlayerControlButton(FButton):
    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setObjectName('mc_btn')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                font-size: 13px;
                color: {1};
                outline: none;
            }}
            #{0}:hover {{
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color4.name())
        self.setStyleSheet(style_str)


class ProgressSlider(_BasicSlider):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)

        self.setOrientation(Qt.Horizontal)
        self.setMinimumWidth(400)
        self.setObjectName('player_progress_slider')

        self.sliderMoved.connect(self.seek)

    def set_duration(self, ms):
        self.setRange(0, ms / 1000)

    def update_state(self, ms):
        self.setValue(ms / 1000)

    def seek(self, second):
        self._app.player.setPosition(second * 1000)


class VolumeSlider(_BasicSlider):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)

        self.setOrientation(Qt.Horizontal)
        self.setMinimumWidth(100)
        self.setObjectName('player_volume_slider')
        self.setRange(0, 100)   # player volume range
        self.setValue(100)
        self.setToolTip('调教播放器音量')


class ProgressLabel(_BasicLabel):
    def __init__(self, app, text=None, parent=None):
        super().__init__(app, text, parent)
        self._app = app

        self.duration_text = '00:00'

        self.setObjectName('player_progress_label')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName(),
                   theme.color3.name())
        self.setStyleSheet(self._style_str + style_str)

    def set_duration(self, ms):
        m, s = parse_ms(ms)
        duration = QTime(0, m, s)
        self.duration_text = duration.toString('mm:ss')

    def update_state(self, ms):
        m, s = parse_ms(ms)
        position = QTime(0, m, s)
        position_text = position.toString('mm:ss')
        self.setText(position_text + '/' + self.duration_text)


class PlayerControlPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.previous_btn = PlayerControlButton(self._app, '上一首', self)
        self.pp_btn = PlayerControlButton(self._app, '播放', self)
        self.next_btn = PlayerControlButton(self._app, '下一首', self)
        self.progress_slider = ProgressSlider(self._app, self)
        self.volume_slider = VolumeSlider(self._app, self)
        self.progress_label = ProgressLabel(self._app, '00:00/00:00', self)

        self._btn_container = FFrame(self)
        self._slider_container = FFrame(self)

        self._bc_layout = QHBoxLayout(self._btn_container)
        self._sc_layout = QHBoxLayout(self._slider_container)

        self.setObjectName('pc_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                color: {1};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color0.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._btn_container.setFixedWidth(140)
        self._slider_container.setMinimumWidth(700)
        self.progress_label.setFixedWidth(80)

        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._bc_layout.setSpacing(0)
        self._bc_layout.setContentsMargins(0, 0, 0, 0)

        self._bc_layout.addWidget(self.previous_btn)
        self._bc_layout.addStretch(1)
        self._bc_layout.addWidget(self.pp_btn)
        self._bc_layout.addStretch(1)
        self._bc_layout.addWidget(self.next_btn)

        self._sc_layout.addWidget(self.progress_slider)
        self._sc_layout.addSpacing(2)
        self._sc_layout.addWidget(self.progress_label)
        self._sc_layout.addSpacing(5)
        self._sc_layout.addStretch(0)
        self._sc_layout.addWidget(self.volume_slider)
        self._sc_layout.addStretch(1)

        self._layout.addWidget(self._btn_container)
        self._layout.addSpacing(10)
        self._layout.addWidget(self._slider_container)


class SongOperationPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setObjectName('song_operation_panel')
        self.set_theme_style()

    def set_theme_style(self):
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName())
        self.setStyleSheet(style_str)


class TopPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.pc_panel = PlayerControlPanel(self._app, self)
        self.mo_panel = SongOperationPanel(self._app, self)

        self.setObjectName('top_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                color: {1};
                border-bottom: 3px inset {3};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color0_light.name(),
                   theme.color0_light.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setFixedHeight(50)
        self._layout.addSpacing(5)
        self._layout.addWidget(self.pc_panel)
        self._layout.addWidget(self.mo_panel)


class LP_LibraryPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.header = LP_GroupHeader(self._app, '我的音乐')
        self.current_playlist_item = LP_GroupItem(self._app, '当前播放列表')
        self.current_playlist_item.set_img_text('❂')
        self._layout = QVBoxLayout(self)

        self.setObjectName('lp_library_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName(),
                   theme.color3.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addSpacing(3)
        self._layout.addWidget(self.header)
        self._layout.addWidget(self.current_playlist_item)

    def add_item(self, item):
        self._layout.addWidget(item)


class LP_PlaylistsPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.header = LP_GroupHeader(self._app, '歌单')
        self._layout = QVBoxLayout(self)
        self.setObjectName('lp_playlists_panel')

        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName(),
                   theme.color5.name())
        self.setStyleSheet(style_str)

    def add_item(self, item):
        self._layout.addWidget(item)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addWidget(self.header)


class LeftPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.library_panel = LP_LibraryPanel(self._app)
        self.playlists_panel = LP_PlaylistsPanel(self._app)

        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)
        self.setObjectName('c_left_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName(),
                   theme.color5.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addWidget(self.library_panel)
        self._layout.addWidget(self.playlists_panel)
        self._layout.addStretch(1)


class LeftPanel_Container(FScrollArea):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.left_panel = LeftPanel(self._app)
        self._layout = QVBoxLayout(self)  # no layout, no children
        self.setWidget(self.left_panel)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        self.setObjectName('c_left_panel_container')
        self.set_theme_style()
        self.setMinimumWidth(180)
        self.setMaximumWidth(220)

        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                border: 0px;
                border-right: 3px inset {1};
            }}
        '''.format(self.objectName(),
                   theme.color0_light.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # self._layout.addWidget(self.left_panel)


class RightPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.widget = None

        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)
        self.setObjectName('right_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName())
        self.setStyleSheet(style_str)

    def set_widget(self, widget):
        if self.widget and self.widget != widget:
            self._layout.removeWidget(self.widget)
            self.widget.hide()
            widget.show()
            self._layout.addWidget(widget)
        else:
            self._layout.addWidget(widget)
        self.widget = widget

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)


class RightPanel_Container(FScrollArea):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.right_panel = RightPanel(self._app)
        self._layout = QVBoxLayout(self)
        self.setWidget(self.right_panel)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        self.setObjectName('c_left_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                border: 0px;
            }}
        '''.format(self.objectName(),
                   theme.color5.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)


class CentralPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.left_panel_container = LeftPanel_Container(self._app, self)
        self.right_panel_container = RightPanel_Container(self._app, self)
        self.left_panel = self.left_panel_container.left_panel
        self.right_panel = self.right_panel_container.right_panel

        self._layout = QHBoxLayout(self)
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addWidget(self.left_panel_container)
        self._layout.addWidget(self.right_panel_container)


class SongLabel(FLabel):
    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setObjectName('song_label')
        self.setIndent(5)
        self.set_theme_style()

        self.set_song('No song is playing')

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.color7.name(),
                   theme.color0.name())
        self.setStyleSheet(style_str)

    def set_song(self, song_text):
        self.setText('♪  ' + song_text + ' ')


class PlaybackModeSwitchBtn(FButton):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setObjectName('player_mode_switch_btn')
        self.set_theme_style()
        self.set_text('循环')

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
                border: 0px;
                padding: 0px 4px;
            }}
        '''.format(self.objectName(),
                   theme.color6.name(),
                   theme.background.name())
        self.setStyleSheet(style_str)

    def set_text(self, text):
        self.setText('♭ ' + text)

    def on_playback_mode_changed(self, playback_mode):
        if playback_mode == PlaybackMode.sequential:
            self.set_text(self._app.player_mode_manager.current_mode.name)
        else:
            self.set_text(playback_mode.value)


class ThemeComboBox(FComboBox):
    clicked = pyqtSignal()
    signal_change_theme = pyqtSignal([str])

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setObjectName('theme_switch_btn')
        self.setEditable(False)
        self.maximum_width = 150
        self.set_theme_style()
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


class PlayerStateLabel(FLabel):
    def __init__(self, app, text=None, parent=None):
        super().__init__('♫', parent)
        self._app = app

        self.setObjectName('player_state_label')
        self.setToolTip('这里显示的是播放器的状态\n'
                        'Buffered 代表该音乐已经可以开始播放\n'
                        'Stalled 表示正在加载或者由于某种原因而被迫中断\n'
                        'Loading 代表正在加载该音乐\n'
                        'Failed 代表加载音乐失败')
        self.set_theme_style()

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
        self.set_theme_style()

    def update_media_state(self, state):
        self.set_theme_style()
        logger.debug('current player media state %d' % state)
        if state == QMediaPlayer.LoadedMedia:
            self.set_text('Loaded')
        elif state == QMediaPlayer.LoadingMedia:
            self.set_text('Loading')
        elif state == QMediaPlayer.BufferingMedia:
            self.set_text('Buffering More')
        elif state == QMediaPlayer.StalledMedia:
            self.set_text('Stalled')
        elif state == QMediaPlayer.BufferedMedia:
            self.set_text('Buffered')
        elif state == QMediaPlayer.InvalidMedia:
            self.set_text('Failed')

    def update_state(self, state):
        return
        self.set_theme_style()
        if state == QMediaPlayer.StoppedState:
            self.set_text('Stopped')
        elif state == QMediaPlayer.PlayingState:
            self.set_text('Playing')
        elif state == QMediaPlayer.PausedState:
            self.set_text('Paused')

    def set_error(self, error):
        self.set_error_style()
        if error == QMediaPlayer.ResourceError:
            self.set_text('Decode Failed')
        elif error == QMediaPlayer.NetworkError:
            self.set_text('Network Error')
        elif error == QMediaPlayer.FormatError:
            self.set_text('Decode Failed')
        elif error == QMediaPlayer.ServiceMissingError:
            self.set_text('Gsteamer Missing')
        else:
            logger.error('player error %d' % error)


class MessageLabel(FLabel):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setObjectName('message_label')
        self._interval = 3
        self.queue = []
        self.hide()

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
            self._interval = 1.2
            return
        if error:
            self._set_error_style()
        else:
            self._set_normal_style()
        self.setText(str(len(self.queue)) + ': ' + text)
        self.show()
        app_event_loop = asyncio.get_event_loop()
        app_event_loop.call_later(self._interval, self.access_message_queue)

    def access_message_queue(self):
        if self.isVisible():
            self.hide()
        if self.queue:
            m = self.queue.pop(0)
            self.show_message(m['message'], m['error'])
        else:
            self._interval = 3


class AppStatusLabel(FLabel):
    clicked = pyqtSignal()

    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setText('♨ Normal'.upper())
        self.setToolTip('点击可以切换到其他模式哦 ~\n'
                        '不过暂时还没实现这个功能...敬请期待 ~')
        self.setObjectName('app_status_label')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {3};
                padding-left: 5px;
                padding-right: 5px;
                font-size: 14px;
            }}
            #{0}:hover {{
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.color4.name(),
                   theme.color2.name(),
                   theme.background.name())
        self.setStyleSheet(style_str)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and \
                self.rect().contains(event.pos()):
            self.clicked.emit()


class NetworkStatus(FLabel):
    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setToolTip('这里显示的是当前网络状态')
        self.setObjectName('network_status_label')
        self.set_theme_style()
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
            painter.drawText(self.rect(), Qt.AlignVCenter,
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


class StatusPanel(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.player_state_label = PlayerStateLabel(self._app)
        self.app_status_label = AppStatusLabel(self._app)
        self.network_status_label = NetworkStatus(self._app)
        self.message_label = MessageLabel(self._app)
        self.song_label = SongLabel(self._app, parent=self)
        self.pms_btn = PlaybackModeSwitchBtn(self._app, self)
        self.theme_switch_btn = ThemeComboBox(self._app, self)

        self.setup_ui()
        self.setObjectName('status_panel')
        self.set_theme_style()

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
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setFixedHeight(18)
        # self.song_label.setMinimumWidth(220)
        self.song_label.setMaximumWidth(300)
        self._layout.addWidget(self.player_state_label)
        self._layout.addWidget(self.app_status_label)
        self._layout.addWidget(self.network_status_label)
        self._layout.addStretch(0)
        self._layout.addWidget(self.message_label)
        self._layout.addStretch(0)
        self._layout.addWidget(self.theme_switch_btn)
        self._layout.addWidget(self.pms_btn)
        self._layout.addWidget(self.song_label)


class CurrentPlaylistTable(MusicTable):
    remove_signal = pyqtSignal([int])   # song id

    def __init__(self, app):
        super().__init__(app)
        self._app = app

        self._row = 0

        self.menu = QMenu()
        self.remove = QAction('从当前列表中移除', self)
        self.menu.addAction(self.remove)

        self.remove.triggered.connect(self.remove_song)

    def contextMenuEvent(self, event):
        point = event.pos()
        item = self.itemAt(point)
        if item is not None:
            row = self.row(item)
            self._row = row
            self.menu.exec(event.globalPos())

    def remove_song(self):
        song = self.songs[self._row]
        self.songs.pop(self._row)
        self.removeRow(self._row)
        self.remove_signal.emit(song.mid)


class LyricFrame(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app


class Ui(object):
    def __init__(self, app):
        self._layout = QVBoxLayout(app)
        self.top_panel = TopPanel(app, app)
        self.central_panel = CentralPanel(app, app)
        self.status_panel = StatusPanel(app, app)
        self.current_playlist_table = CurrentPlaylistTable(app)

        self.setup()

    def setup(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.top_panel)
        self._layout.addWidget(self.central_panel)
        self._layout.addWidget(self.status_panel)
