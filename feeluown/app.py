# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QBrush
from PyQt5.QtMultimedia import QMediaPlayer

from .consts import DEFAULT_THEME_NAME
from .player import Player
from .plugin import PluginsManager
from .theme import ThemeManager
from .ui import Ui
from .utils import pixmap_from_url, darker
from feeluown.libs.widgets.base import FFrame


class App(FFrame):
    def __init__(self):
        super().__init__()
        self.player = Player(self)
        self.theme_manager = ThemeManager(self)
        self.plugins_manager = PluginsManager(self)
        self.theme_manager.set_theme(DEFAULT_THEME_NAME)

        self.ui = Ui(self)
        self._init_managers()

        self.player_pixmap = None

        self.resize(960, 600)
        self.setObjectName('app')
        self.set_theme_style()

        self.bind_signal()
        self.test()

    def bind_signal(self):
        top_panel = self.ui.top_panel

        self.player.stateChanged.connect(self._on_player_status_changed)
        self.player.positionChanged.connect(self._on_player_position_changed)
        self.player.durationChanged.connect(self._on_player_duration_changed)
        self.player.signal_player_media_changed.connect(
            self._on_player_song_changed)

        top_panel.pc_panel.volume_slider.sliderMoved.connect(self.change_volume)
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

    def test(self):
        self.theme_manager.choose('Molokai')
        # self.theme_manager.choose('Tomorrow Night')

    def _on_player_duration_changed(self, ms):
        self.ui.top_panel.pc_panel.progress_label.set_duration(ms)
        self.ui.top_panel.pc_panel.progress_slider.set_duration(ms)

    def _on_player_position_changed(self, ms):
        self.ui.top_panel.pc_panel.progress_label.update_state(ms)
        self.ui.top_panel.pc_panel.progress_slider.update_state(ms)

    def _on_player_song_changed(self, song):
        song_label = self.ui.status_panel.song_label
        song_label.set_song(song.title + ' - ' + song.artists_name)
        self.player_pixmap = pixmap_from_url(song.album_img)
        self.update()

    def _on_player_status_changed(self, status):
        pp_btn = self.ui.top_panel.pc_panel.pp_btn
        if status == QMediaPlayer.PlayingState:
            pp_btn.setText('暂停')
        else:
            pp_btn.setText('播放')

    def change_volume(self, value):
        self.player.setVolume(value)
        pass
