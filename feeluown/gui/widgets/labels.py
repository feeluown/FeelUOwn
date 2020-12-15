from PyQt5.QtCore import QTime, Qt
from PyQt5.QtWidgets import QLabel

from feeluown.utils.utils import parse_ms


class DurationLabel(QLabel):
    def __init__(self, app, parent=None):
        super().__init__('00：00', parent=parent)
        self._app = app

        self.setAlignment(Qt.AlignCenter)
        self._app.player.duration_changed.connect(
            self.on_duration_changed, aioqueue=True)

    def on_duration_changed(self, duration):
        duration = duration * 1000
        m, s = parse_ms(duration)
        t = QTime(0, m, s)
        self.setText(t.toString('mm:ss'))


class ProgressLabel(QLabel):
    def __init__(self, app, parent=None):
        super().__init__('00：00', parent=parent)
        self._app = app

        self.setAlignment(Qt.AlignCenter)
        self._app.player.position_changed.connect(
            self.on_position_changed, aioqueue=True)

    def on_position_changed(self, position):
        if position is None:
            return
        position = position * 1000
        m, s = parse_ms(position)
        t = QTime(0, m, s)
        self.setText(t.toString('mm:ss'))
