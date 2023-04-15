from PyQt5.QtCore import QTime, Qt
from PyQt5.QtWidgets import QLabel

from feeluown.utils.utils import parse_ms


def format_second(s):
    """Format mileseconds to text

    >>> format_second(1)
    '00:01'
    """
    m, s = parse_ms(s * 1000)
    h = m // 60
    m = m % 60
    t = QTime(h, m, s)
    if h > 0:
        text = t.toString('hh:mm:ss')
    else:
        text = t.toString('mm:ss')
    return text


class DurationLabel(QLabel):
    def __init__(self, app, parent=None):
        super().__init__('00:00', parent=parent)
        self._app = app

        self.setAlignment(Qt.AlignCenter)
        self._app.player.duration_changed.connect(
            self.on_duration_changed, aioqueue=True)

    def on_duration_changed(self, duration):
        self.setText(format_second(duration or 0))


class ProgressLabel(QLabel):
    def __init__(self, app, parent=None):
        super().__init__('00:00', parent=parent)
        self._app = app

        self.setAlignment(Qt.AlignCenter)
        self._app.player_pos_per300ms.changed.connect(self.on_position_changed)

    def on_position_changed(self, position):
        self.setText(format_second(position or 0))
