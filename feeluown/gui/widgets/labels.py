from PyQt5.QtCore import QTime, Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QLabel, QSizePolicy

from feeluown.utils.utils import parse_ms
from feeluown.gui.helpers import elided_text, SOLARIZED_COLORS


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


class ElidedLineLabel(QLabel):
    """Label whose text is auto elided based on its width.

    .. versionadded:: 3.8.15
    """
    def __init__(self, text='', **kwargs):
        super().__init__(text, **kwargs)
        self._src_text = text
        self.setWordWrap(False)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        # Set horizental size policy to Preferred so that this label
        # can shrink or expand when the parent is resized.
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    def set_src_text(self, text):
        self._src_text = text
        self._auto_adjust_text()

    def _auto_adjust_text(self):
        text = elided_text(self._src_text, self.width(), self.font())
        self.setText(text)

    def resizeEvent(self, e):
        self._auto_adjust_text()
        return super().resizeEvent(e)


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


class MessageLabel(QLabel):
    """Show warning/error message.
    """
    INFO = 'info'
    ERROR = 'error'

    def __init__(self, text='', level=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWordWrap(True)
        self.show_msg(text, level)

    def show_msg(self, text, level=None):
        if level == MessageLabel.ERROR:
            hint = '错误提示：'
            color = 'red'
        elif level == MessageLabel.INFO:
            hint = '️提示：'
            color = SOLARIZED_COLORS['blue']
        else:
            hint = '️'
            color = SOLARIZED_COLORS['blue']
        palette = self.palette()
        palette.setColor(QPalette.Text, QColor(color))
        palette.setColor(QPalette.WindowText, QColor(color))
        self.setPalette(palette)
        self.setText(f"{hint}{text}")
