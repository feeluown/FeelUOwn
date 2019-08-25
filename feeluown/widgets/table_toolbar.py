from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
)


class SongsTableToolbar(QWidget):
    _desc_btn_checked_text = '折叠'
    _desc_btn_unchecked_text = '展开描述'

    play_all_needed = pyqtSignal()
    toggle_desc_needed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.play_all_btn = QPushButton('播放全部', self)
        self.desc_btn = QPushButton(self._desc_btn_unchecked_text, self)
        self.play_all_btn.clicked.connect(self.play_all_needed.emit)
        self.desc_btn.clicked.connect(self.on_desc_btn_toggled)
        self._setup_ui()

    def _setup_ui(self):
        self.desc_btn.hide()

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.play_all_btn)
        self._layout.addSpacing(5)
        self._layout.addWidget(self.desc_btn)
        self._layout.addStretch(1)

    def on_desc_btn_toggled(self, checked):
        if checked:
            self.play_all_btn.hide()
            self.desc_btn.setText(self._desc_btn_checked_text)
        else:
            self.play_all_btn.show()
            self.desc_btn.setText(self._desc_btn_unchecked_text)
        self.toggle_desc_needed.emit()
