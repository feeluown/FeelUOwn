from PyQt5.QtCore import Qt, QObject, QCoreApplication, QEvent
from PyQt5.QtGui import QKeySequence as KS
from PyQt5.QtWidgets import QShortcut as Sc

from feeluown.player import State


class HotkeyManager(QObject):
    """集中管理各个组件的快捷键"""

    def __init__(self, app):
        super().__init__(app)
        self._app = app

    def initialize(self):
        app = self._app
        ui = self._app.ui

        # magicbox
        Sc(KS('Ctrl+F'), app).activated.connect(ui.magicbox.setFocus)

        # player
        Sc(KS(Qt.Key_Space), app).activated.connect(app.player.toggle)
        Sc(KS(Qt.Key_Right), app).activated.connect(self._player_forward_a_little)
        Sc(KS(Qt.Key_Left), app).activated.connect(self._player_backward_a_little)
        Sc(KS(Qt.Key_Up), app).activated.connect(self._player_volume_up_a_little)
        Sc(KS(Qt.Key_Down), app).activated.connect(self._player_volume_down_a_little)

        # browser
        Sc(KS.Back, app).activated.connect(app.browser.back)
        Sc(KS.Forward, app).activated.connect(app.browser.forward)

        # install event filter on app
        q_app = QCoreApplication.instance()
        q_app.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            button = event.button()
            if button == Qt.BackButton:
                self._app.browser.back()
                return True
            elif button == Qt.ForwardButton:
                self._app.browser.forward()
                return True
        return False

    def _player_forward_a_little(self):
        if self._app.player.state in (State.paused, State.playing):
            self._app.player.position = min(self._app.player.duration - 1,
                                            self._app.player.position + 5)

    def _player_backward_a_little(self):
        if self._app.player.state in (State.paused, State.playing):
            self._app.player.position = max(0,
                                            self._app.player.position - 5)

    def _player_volume_up_a_little(self):
        self._app.player.volume = min(100,
                                      self._app.player.volume + 10)

    def _player_volume_down_a_little(self):
        self._app.player.volume = max(0,
                                      self._app.player.volume - 10)
