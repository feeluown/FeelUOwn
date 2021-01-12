from PyQt5.QtCore import Qt, QObject, QCoreApplication, QEvent
from PyQt5.QtGui import QKeySequence as KS
from PyQt5.QtWidgets import QShortcut


class HotkeyManager(QObject):
    """集中管理各个组件的快捷键"""

    def __init__(self, app):
        super().__init__(app)
        self._app = app

    def initialize(self):
        app = self._app
        ui = self._app.ui

        # magicbox
        QShortcut(KS('Ctrl+F'), app).activated.connect(ui.magicbox.setFocus)

        # player
        QShortcut(KS(Qt.Key_Space), app).activated.connect(app.player.toggle)

        def p_shortcut_connect(k, cb):  # an alias to simplify code
            sc = QShortcut(KS(k), ui.pc_panel)
            sc.setContext(Qt.WidgetWithChildrenShortcut)
            sc.activated.connect(cb)

        p_shortcut_connect(Qt.Key_Right, self._player_forward_a_little)
        p_shortcut_connect(Qt.Key_Left, self._player_backward_a_little)
        p_shortcut_connect(Qt.Key_Up, self._player_volume_up_a_little)
        p_shortcut_connect(Qt.Key_Down, self._player_volume_down_a_little)

        # browser
        QShortcut(KS.Back, app).activated.connect(app.browser.back)
        QShortcut(KS.Forward, app).activated.connect(app.browser.forward)

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
        old_position = self._app.player.position
        duration = self._app.player.duration
        if None not in (old_position, duration):
            self._app.player.position = min(duration - 1, old_position + 5)

    def _player_backward_a_little(self):
        old_position = self._app.player.position
        if old_position is not None:
            self._app.player.position = max(0, old_position - 5)

    def _player_volume_up_a_little(self):
        self._app.player.volume = min(100,
                                      self._app.player.volume + 10)

    def _player_volume_down_a_little(self):
        self._app.player.volume = max(0,
                                      self._app.player.volume - 10)
