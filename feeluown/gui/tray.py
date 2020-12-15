import sys

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QAction, QMenu, QApplication

from feeluown.player import State
from feeluown.gui.helpers import elided_text


TOGGLE_APP_TEXT = ('激活主窗口', '隐藏主窗口')
TOGGLE_PLAYER_TEXT = ('播放', '暂停')

IS_MACOS = sys.platform == 'darwin'


class Tray(QSystemTrayIcon):
    def __init__(self, app):
        """
        type app: feeluown.app.App
        """
        super().__init__()
        self._app = app
        self._app_old_state = None  #: app window state before minimized

        # setup context menu
        self._menu = QMenu()
        self._status_action = QAction('...')
        self._toggle_player_action = QAction(QIcon.fromTheme('media-play'),
                                             TOGGLE_PLAYER_TEXT[0])
        self._next_action = QAction(QIcon.fromTheme('media-skip-forward'), '下一首')
        self._prev_action = QAction(QIcon.fromTheme('media-skip-backward'), '上一首')
        self._quit_action = QAction(QIcon.fromTheme('exit'), '退出')
        # add toggle_app action for macOS, on other platforms, user
        # can click the tray icon to toggle_app
        if IS_MACOS:
            self._toggle_app_action = QAction(QIcon.fromTheme('window'),
                                              TOGGLE_APP_TEXT[1])
        else:
            self._toggle_app_action = None
            self.activated.connect(self._toggle_app_state) # noqa

        # bind signals
        self._quit_action.triggered.connect(self._app.exit)
        self._toggle_player_action.triggered.connect(self._app.player.toggle)
        self._prev_action.triggered.connect(self._app.playlist.previous)
        self._next_action.triggered.connect(self._app.playlist.next)
        if self._toggle_app_action is not None:
            self._toggle_app_action.triggered.connect(self._toggle_app_state)
        self._app.player.state_changed.connect(self.on_player_state_changed)
        self._app.playlist.song_changed.connect(self.on_player_song_changed)
        self._app.theme_mgr.theme_changed.connect(self.on_theme_changed)
        q_app = QApplication.instance()
        q_app.applicationStateChanged.connect(self.on_app_state_changed)

        self._app.installEventFilter(self)
        self.setContextMenu(self._menu)
        self.setup_ui()

    def initialize(self):
        self._set_icon()
        self._status_action.setIcon(self.icon())
        self.show()

    def setup_ui(self):
        self._menu.addAction(self._status_action)
        self._menu.addAction(self._toggle_player_action)
        self._menu.addAction(self._prev_action)
        self._menu.addAction(self._next_action)
        self._menu.addSeparator()
        if self._toggle_app_action is not None:
            self._menu.addAction(self._toggle_app_action)
        self._menu.addAction(self._quit_action)
        self._status_action.setEnabled(False)

    def _toggle_app_state(self):
        """activate/deactivate app"""
        if self._app.isHidden():
            self._app.show()
            self._app.activateWindow()
        elif self._app.isMinimized():
            self._app.setWindowState(self._app_old_state)
        else:
            self._app.hide()

    def _set_icon(self):
        # respect system icon
        icon = QIcon.fromTheme('feeluown-tray',
                               QIcon(self._app.theme_mgr.get_icon('tray')))
        self.setIcon(icon)

    def on_theme_changed(self, _):
        self._set_icon()

    def on_player_song_changed(self, song):
        if song is not None:
            status = f'{song.title_display} - {song.artists_name_display}'
            if self._app.config.NOTIFY_ON_TRACK_CHANGED:
                # TODO: show song cover if possible
                self.showMessage(song.title_display,
                                 song.artists_name_display,
                                 msecs=self._app.config.NOTIFY_DURATION)
            self._status_action.setText(elided_text(status, 120))
            self._status_action.setToolTip(status)
            self.setToolTip(status)

    def on_player_state_changed(self, state):
        if state == State.playing:
            self._toggle_player_action.setText(TOGGLE_PLAYER_TEXT[1])
            self._toggle_player_action.setIcon(QIcon.fromTheme('media-pause'))
            self._toggle_player_action.setEnabled(True)
        else:
            self._toggle_player_action.setText(TOGGLE_PLAYER_TEXT[0])
            self._toggle_player_action.setIcon(QIcon.fromTheme('media-play'))
            if state == State.stopped:
                self._toggle_player_action.setEnabled(False)
            else:
                self._toggle_player_action.setEnabled(True)

    def on_app_state_changed(self, state):
        if state == Qt.ApplicationActive:
            # On macOS, when the app is hidden, there will be an icon on the
            # macOS dock, if user click the dock, we should activate the app window.
            # For other platforms(Win32/Linux), the dock icon is not visible if
            # the window is hidden/closed.
            #
            # When the state will be changed to QApplicationActive?
            # * the dock icon is clicked (on macOS)
            # * the Qt.Tool widget got focus (on macOS and Linux)
            # * the Qt.Window widget got focus (on Linux)
            if IS_MACOS:
                self._app.show()
                self._app.activateWindow()
        elif state == Qt.ApplicationInactive:
            # when app window is not the top window, it changes to inactive
            if self._toggle_app_action is not None:
                self._toggle_app_action.setText(TOGGLE_APP_TEXT[0])

    def eventFilter(self, obj, event):
        """event filter for app"""
        app_text_idx = None
        if event.type() == QEvent.WindowStateChange:
            # when window is maximized before minimized, the window state will
            # be Qt.WindowMinimized | Qt.WindowMaximized
            if obj.windowState() & Qt.WindowMinimized:
                self._app_old_state = event.oldState()
                app_text_idx = 0
            else:
                app_text_idx = 1
        elif event.type() == QEvent.Hide:
            app_text_idx = 0
        elif event.type() == QEvent.Show:
            app_text_idx = 1
        if app_text_idx is not None and self._toggle_app_action is not None:
            self._toggle_app_action.setText(TOGGLE_APP_TEXT[app_text_idx])
        return False
