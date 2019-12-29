from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QScrollArea, QFrame, QLabel, QVBoxLayout


class DescriptionContainer(QScrollArea):

    space_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.RichText)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setWidget(self.label)
        self.setToolTip('按空格可以窗口全屏')

        self._setup_ui()

    def _setup_ui(self):
        self.label.setAlignment(Qt.AlignTop)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def keyPressEvent(self, event):
        key_code = event.key()
        if key_code == Qt.Key_J:
            value = self.verticalScrollBar().value()
            self.verticalScrollBar().setValue(value + 20)
        elif key_code == Qt.Key_K:
            value = self.verticalScrollBar().value()
            self.verticalScrollBar().setValue(value - 20)
        elif key_code == Qt.Key_Space:
            self.space_pressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def set_body(self, text):
        self.label.setText(text)
