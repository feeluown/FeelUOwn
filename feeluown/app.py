# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QImage, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtMultimedia import QMediaPlayer

from .consts import DEFAULT_THEME_NAME, APP_ICON
from .hotkey import Hotkey
from .player import Player
from .plugin import PluginsManager
from .request import Request
from .theme import ThemeManager
from .ui import Ui
from .utils import darker
from feeluown.libs.widgets.base import FFrame


class App(FFrame):
    def __init__(self):
        super().__init__()
        self.player = Player(self)
        self.request = Request(self)
        self.theme_manager = ThemeManager(self)
        self.hotkey_manager = Hotkey(self)
        self.plugins_manager = PluginsManager(self)
        self.theme_manager.set_theme(DEFAULT_THEME_NAME)

        self.ui = Ui(self)
        self._init_managers()

        self.player_pixmap = None

        self.resize(960, 600)
        self.setObjectName('app')
        QApplication.setWindowIcon(QIcon(APP_ICON))
        self.set_theme_style()

        self.bind_signal()
        self.test()

    def bind_signal(self):
        top_panel = self.ui.top_panel
        status_panel = self.ui.status_panel

        self.player.stateChanged.connect(self._on_player_status_changed)
        self.player.positionChanged.connect(self._on_player_position_changed)
        self.player.durationChanged.connect(self._on_player_duration_changed)
        self.player.signal_player_media_changed.connect(
            self._on_player_song_changed)
        self.player.mediaStatusChanged.connect(
            status_panel.player_state_label.update_media_state)
        self.player.stateChanged.connect(
            status_panel.player_state_label.update_state)
        self.player.error.connect(status_panel.player_state_label.set_error)
        self.player.signal_playback_mode_changed.connect(
            status_panel.pms_btn.on_playback_mode_changed)

        status_panel.pms_btn.clicked.connect(self.player.next_playback_mode)

        self.request.connected_signal.connect(self._on_network_connected)
        self.request.disconnected_signal.connect(self._on_network_disconnected)
        self.request.slow_signal.connect(self._on_network_slow)

        top_panel.pc_panel.volume_slider.sliderMoved.connect(
            self.change_volume)
        top_panel.pc_panel.pp_btn.clicked.connect(self.player.play_or_pause)
        top_panel.pc_panel.next_btn.clicked.connect(self.player.play_next)
        top_panel.pc_panel.previous_btn.clicked.connect(self.player.play_last)

    def paintEvent(self, event):
        painter = QPainter(self)
        bg_color = darker(self.theme_manager.current_theme.background, a=200)

        if self.player_pixmap is not None:
            pixmap = self.player_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, pixmap)
            painter.fillRect(self.rect(), bg_color)

    def _init_managers(self):
        self.plugins_manager.scan()

    def set_theme_style(self):
        theme = self.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.background.name(),
                   theme.foreground.name())
        self.setStyleSheet(style_str)

    def message(self, text, error=False):
        self.ui.status_panel.message_label.show_message(text, error)

    def notify(self, text, error=False):
        pass

    def test(self):
        # self.theme_manager.choose('Molokai')
        # self.theme_manager.choose('Tomorrow Night')
        pass

    def _on_player_duration_changed(self, ms):
        self.ui.top_panel.pc_panel.progress_label.set_duration(ms)
        self.ui.top_panel.pc_panel.progress_slider.set_duration(ms)

    def _on_player_position_changed(self, ms):
        self.ui.top_panel.pc_panel.progress_label.update_state(ms)
        self.ui.top_panel.pc_panel.progress_slider.update_state(ms)

    def _on_player_song_changed(self, song):
        song_label = self.ui.status_panel.song_label
        song_label.set_song(song.title + ' - ' + song.artists_name)
        self.player_pixmap = self.pixmap_from_url(song.album_img)
        if self.player_pixmap is not None:
            QApplication.setWindowIcon(QIcon(self.player_pixmap))
        self.update()

    def _on_player_status_changed(self, status):
        pp_btn = self.ui.top_panel.pc_panel.pp_btn
        if status == QMediaPlayer.PlayingState:
            pp_btn.setText('暂停')
        else:
            pp_btn.setText('播放')

    def _on_network_slow(self):
        network_status_label = self.ui.status_panel.network_status_label
        network_status_label.set_state(0)

    def _on_network_connected(self):
        network_status_label = self.ui.status_panel.network_status_label
        network_status_label.set_state(1)

    def _on_network_disconnected(self):
        network_status_label = self.ui.status_panel.network_status_label
        network_status_label.set_state(0)

    def change_volume(self, value):
        self.player.setVolume(value)

    def pixmap_from_url(self, url, callback=None):
        res = self.request.get(url)
        if res is None:
            return None
        img = QImage()
        img.loadFromData(res.content)
        if callback is not None:
            callback(QPixmap(img))
            return None
        else:
            return QPixmap(img)

    def closeEvent(self, event):
        self.player.stop()
        QApplication.quit()
