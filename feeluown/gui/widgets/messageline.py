from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout

from feeluown.gui.helpers import BgTransparentMixin, elided_text


class MessageLine(QWidget, BgTransparentMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.hide)

        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)

        self._setup_ui()

    def _setup_ui(self):
        # Fill the background with QPalette.Highlight color.
        #
        # Note(@cosven): I found that even the BackgroundRole is set to a
        # color with alpha, the background can't be semi-transparent.
        self.setBackgroundRole(QPalette.Highlight)
        self.setForegroundRole(QPalette.HighlightedText)
        self.setAutoFillBackground(True)

        self.setMaximumHeight(25)
        self._layout = QHBoxLayout(self)
        self._layout.addStretch(0)
        self._layout.addWidget(self._label)
        self._layout.setStretchFactor(self._label, 1)
        self._layout.addStretch(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def show_msg(self, msg, timeout=1500, **kwargs):
        self._label.setText(elided_text(msg, self.width(), self.font()))
        self.show()
        self._timer.start(timeout)
