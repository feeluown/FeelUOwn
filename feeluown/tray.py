import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QAction, QMenu

from fuocore.player import State


class Tray:
    ACTIONS = {
        'current': ('', None, False),
        'toggle': ('&Play', 'media-play', False),
        'quit': ('&Quit FeelUOwn', 'exit', True)
    }

    def __init__(self, app):
        # init
        self._app = app
        self._player = app.player
        self._playlist = app.player.playlist
        self.tray_icon = QSystemTrayIcon()
        self.context_menu = QMenu()
        # create menu, icon and connect signals
        self.create_menu()
        self.create_icon()
        self.connect_signals()

    def create_menu(self):
        for alias, action in self.ACTIONS.items():
            setattr(self, alias + '_action', QAction(action[0]))
            getattr(self, alias + '_action').setEnabled(action[2])
            if action[1] is not None:
                getattr(self, alias + '_action').setIcon(QIcon.fromTheme(action[1]))
            getattr(self, alias + '_action').triggered.connect(getattr(self, 'trigger_' + alias, self.trigger_default))
            self.context_menu.addAction(getattr(self, alias + '_action'))
        self.tray_icon.setContextMenu(self.context_menu)

    def create_icon(self):
        cpath = os.path.dirname(__file__)
        self.tray_icon.setIcon(QIcon.fromTheme('feeluowntray', QIcon(f'{cpath}/tray.png')))
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()

    def trigger_quit(self):
        self._app.close()

    def trigger_default(self):
        # reserved for general trigger actions
        pass

    def trigger_toggle(self):
        if self._player.state == State.playing:
            self._player.pause()
        elif self._player.state == State.paused:
            self._player.resume()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self._app.isHidden():
                self._app.show()
                self._app.activateWindow()
            elif self._app.isActiveWindow():
                self._app.hide()
            else:
                self._app.activateWindow()

    def connect_signals(self):
        self._player.state_changed.connect(self.state_changed)
        self._playlist.song_changed.connect(self.song_changed)

    def song_changed(self, song):
        if song is not None:
            title = f'{song.title_display} - {song.artists_name}'[0:30]
            self.current_action.setText(title)
            self.tray_icon.setToolTip(title)

    def state_changed(self, state):
        if state == State.playing:
            self.toggle_action.setText('&Pause')
            self.toggle_action.setIcon(QIcon.fromTheme('media-pause'))
            self.toggle_action.setEnabled(True)
        elif state == State.paused:
            self.toggle_action.setText('&Play')
            self.toggle_action.setIcon(QIcon.fromTheme('media-play'))
            self.toggle_action.setEnabled(True)
        else:
            self.toggle_action.setText('&Play')
            self.toggle_action.setIcon(QIcon.fromTheme('media-play'))
            self.toggle_action.setEnabled(False)
