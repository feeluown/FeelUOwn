from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QPushButton, QWidget, QComboBox,
                             QLineEdit)

from fuocore.models import AlbumType


class SongsTableToolbar(QWidget):
    play_all_needed = pyqtSignal()
    filter_albums_needed = pyqtSignal([list])
    filter_text_changed = pyqtSignal([str])

    def __init__(self, parent=None):
        super().__init__(parent)

        self.play_all_btn = QPushButton('播放全部', self)
        self.filter_box = QLineEdit(parent=self)
        self.filter_box.setPlaceholderText('输入关键词进行过滤')
        self.filter_box.setMinimumHeight(25)
        self.filter_box.textChanged.connect(self.filter_text_changed)
        self.play_all_btn.clicked.connect(self.play_all_needed.emit)

        # album filters
        self.filter_albums_combobox = QComboBox(self)
        self.filter_albums_combobox.addItems(['所有专辑', '标准', '单曲与EP', '现场', '合辑'])
        self.filter_albums_combobox.currentIndexChanged.connect(
            self.on_albums_filter_changed)
        # 8 works on macOS, don't know if it works on various Linux DEs
        self.filter_albums_combobox.setMinimumContentsLength(8)
        self.filter_albums_combobox.hide()
        self._setup_ui()

    def before_change_mode(self):
        """filter all filter buttons"""
        self.filter_albums_combobox.hide()
        self.play_all_btn.hide()

    def albums_mode(self):
        self.before_change_mode()
        self.filter_albums_combobox.show()

    def songs_mode(self):
        self.before_change_mode()
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
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.play_all_btn)
        self._layout.addStretch(0)
        self._layout.addWidget(self.filter_albums_combobox)
        self._layout.addStretch(0)
        self._layout.addWidget(self.filter_box)

    def on_albums_filter_changed(self, index):
        # ['所有', '专辑', '单曲与EP', '现场', '合辑']
        if index == 0:
            types = []
        elif index == 1:
            types = [AlbumType.standard]
        elif index == 2:
            types = [AlbumType.single, AlbumType.ep]
        elif index == 3:
            types = [AlbumType.live]
        else:
            types = [AlbumType.compilation, AlbumType.retrospective]
        self.filter_albums_needed.emit(types)
