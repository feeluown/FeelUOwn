from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QRadioButton,
    QWidget,
)


class SongsTableToolbar(QWidget):
    _desc_btn_checked_text = '折叠'
    _desc_btn_unchecked_text = '展开描述'

    play_all_needed = pyqtSignal()
    show_songs_needed = pyqtSignal()
    show_albums_needed = pyqtSignal()
    # show_videos_needed = pyqtSignal()

    # album filters
    filter_albums_mini_needed = pyqtSignal()
    filter_albums_contributed_needed = pyqtSignal()
    filter_albums_live_needed = pyqtSignal()
    filter_albums_all_needed = pyqtSignal()

    toggle_desc_needed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.play_all_btn = QPushButton('播放全部', self)
        self.show_songs_btn = QPushButton('歌曲', parent=self)
        self.show_albums_btn = QPushButton('专辑', parent=self)
        # self.show_videos_btn = QPushButton(parent=self)
        self.desc_btn = QPushButton(self._desc_btn_unchecked_text, self)
        self.play_all_btn.clicked.connect(self.play_all_needed.emit)
        self.show_songs_btn.clicked.connect(self.show_songs_needed.emit)
        self.show_albums_btn.clicked.connect(self.show_albums_needed.emit)
        # self.show_videos_btn.clicked.connect(self.show_videos_needed.emit)
        self.desc_btn.clicked.connect(self.on_desc_btn_toggled)

        # album filters
        self.filter_albums_all_btn = QRadioButton('所有', parent=self)
        self.filter_albums_mini_btn = QRadioButton('单曲与EP', parent=self)
        self.filter_albums_contributed_btn = QRadioButton('参与作品', parent=self)
        self.filter_albums_live_btn = QRadioButton('现场', parent=self)

        self.filter_albums_all_btn.clicked.connect(self.filter_albums_all_needed.emit)
        self.filter_albums_mini_btn.clicked.connect(self.filter_albums_mini_needed.emit)
        self.filter_albums_contributed_btn.clicked.connect(
            self.filter_albums_contributed_needed.emit)
        self.filter_albums_live_btn.clicked.connect(self.filter_albums_live_needed.emit)

        self.show_songs_btn.hide()
        self.show_albums_btn.hide()
        self.desc_btn.hide()
        self.filter_albums_mini_btn.hide()
        self.filter_albums_contributed_btn.hide()
        self.filter_albums_all_btn.hide()
        self.filter_albums_live_btn.hide()
        self._setup_ui()

    def before_change_mode(self):
        """filter all filter buttons"""
        self.filter_albums_mini_btn.hide()
        self.filter_albums_contributed_btn.hide()
        self.filter_albums_all_btn.hide()
        self.filter_albums_live_btn.hide()

    def artist_mode(self):
        self.before_change_mode()
        self.play_all_btn.show()
        self.show_songs_btn.show()
        self.show_albums_btn.show()

    def albums_mode(self):
        self.before_change_mode()
        self.play_all_btn.hide()
        self.show_albums_btn.show()
        self.filter_albums_mini_btn.show()
        self.filter_albums_contributed_btn.show()
        self.filter_albums_all_btn.show()
        self.filter_albums_live_btn.show()

    def songs_mode(self):
        self.before_change_mode()
        self.play_all_btn.show()

    def pure_songs_mode(self):
        """playlist/collections mode"""
        self.before_change_mode()
        self.show_albums_btn.hide()
        self.show_songs_btn.hide()
        self.play_all_btn.show()

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
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addWidget(self.play_all_btn)
        self._layout.addSpacing(5)
        self._layout.addWidget(self.show_songs_btn)
        self._layout.addSpacing(5)
        self._layout.addWidget(self.show_albums_btn)

        self._layout.addStretch(1)

        self._layout.addWidget(self.filter_albums_all_btn)
        self._layout.addWidget(self.filter_albums_mini_btn)
        self._layout.addWidget(self.filter_albums_live_btn)
        self._layout.addWidget(self.filter_albums_contributed_btn)

        self._layout.addStretch(1)

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
