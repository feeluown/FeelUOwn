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
    show_songs_needed = pyqtSignal()
    show_albums_needed = pyqtSignal()
    toggle_desc_needed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.play_all_btn = QPushButton('播放全部', self)
        self.show_songs_btn = QPushButton(parent=self)
        self.show_albums_btn = QPushButton(parent=self)
        self.desc_btn = QPushButton(self._desc_btn_unchecked_text, self)
        self.play_all_btn.clicked.connect(self.play_all_needed.emit)
        self.desc_btn.clicked.connect(self.on_desc_btn_toggled)
        self.show_albums_btn.clicked.connect(self.show_albums_needed.emit)
        self.show_songs_btn.clicked.connect(self.show_songs_needed.emit)

        self.show_songs_btn.hide()
        self.show_albums_btn.hide()
        self._setup_ui()

    def artist_mode(self):
        self.show_songs_btn.setText('歌曲')
        self.show_albums_btn.setText('专辑')
        self.show_songs_btn.show()
        self.show_albums_btn.show()

    def songs_mode(self):
        self.show_songs_btn.hide()
        self.show_albums_btn.hide()

    def enter_state_playall_start(self):
        self.play_all_btn.setEnabled(False)
        # currently, this is called only when feeluown is fetching songs,
        # so when we enter state_playall_start, we set play all btn text
        # to this.
        self.play_all_btn.setText('正在获取全部歌曲...')

    def enter_state_playall_end(self):
        self.play_all_btn.setText('正在获取全部歌曲...done')
        self.play_all_btn.setEnabled(True)
        self.play_all_btn.setText('播放全部')

    def _setup_ui(self):
        self.desc_btn.hide()

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.play_all_btn)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.show_songs_btn)
        self._layout.addSpacing(5)
        self._layout.addWidget(self.show_albums_btn)
        self._layout.addStretch(10)
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
