import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QAction, QMenu

from fuocore.player import State


class Tray:
    ACTIONS = {
        'current': ('', 'feeluowntray', False),
        'toggle': ('&Play', 'media-play', False),
        'next': ('&Next', 'media-skip-forward', False),
        'prev': ('&Prev', 'media-skip-backward', False),
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
                if action[1] == 'feeluowntray':
                    cpath = os.path.dirname(__file__)
                    getattr(self, alias + '_action').setIcon(QIcon.fromTheme(action[1], QIcon(f'{cpath}/tray.png'))) # noqa
                else:
                    getattr(self, alias + '_action').setIcon(QIcon.fromTheme(action[1])) # noqa
            getattr(self, alias + '_action').triggered.connect(getattr(self, 'trigger_' + alias, self.trigger_default))
            self.context_menu.addAction(getattr(self, alias + '_action'))
        self.tray_icon.setContextMenu(self.context_menu)

    def create_icon(self):
        cpath = os.path.dirname(__file__)
        self.tray_icon.setIcon(QIcon.fromTheme('feeluowntray', QIcon(f'{cpath}/tray.png'))) # noqa
        self.tray_icon.activated.connect(self.tray_activated) # noqa
        self.tray_icon.show()

    def trigger_quit(self):
        self._app.exit()

    def trigger_default(self):
        # reserved for general trigger actions
        pass

    def trigger_toggle(self):
        if self._player.state == State.playing:
            self._player.pause()
        elif self._player.state == State.paused:
            self._player.resume()

    def trigger_next(self):
        if self._player.state != State.stopped:
            self._playlist.next()

    def trigger_prev(self):
        if self._player.state != State.stopped:
            self._playlist.previous()

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
            if self._app.config.NOTIFY_ON_TRACK_CHANGED:
                cpath = os.path.dirname(__file__)
                self.tray_icon.showMessage(song.title_display, song.artists_name, QIcon(f'{cpath}/feeluown.png'),
                                           self._app.config.NOTIFY_DURATION)
            self.current_action.setText(title) # noqa
            self.tray_icon.setToolTip(title)

    def state_changed(self, state):
        if state == State.playing:
            self.toggle_action.setText('&Pause') # noqa
            self.toggle_action.setIcon(QIcon.fromTheme('media-pause')) # noqa
            self.toggle_action.setEnabled(True) # noqa
            self.next_action.setEnabled(True) # noqa
            self.prev_action.setEnabled(True) # noqa
        elif state == State.paused:
            self.toggle_action.setText('&Play') # noqa
            self.toggle_action.setIcon(QIcon.fromTheme('media-play')) # noqa
            self.toggle_action.setEnabled(True) # noqa
            self.next_action.setEnabled(True) # noqa
            self.prev_action.setEnabled(True) # noqa
        else:
            self.toggle_action.setText('&Play') # noqa
            self.toggle_action.setIcon(QIcon.fromTheme('media-play')) # noqa
            self.toggle_action.setEnabled(False) # noqa
            self.next_action.setEnabled(False) # noqa
            self.prev_action.setEnabled(False) # noqa
