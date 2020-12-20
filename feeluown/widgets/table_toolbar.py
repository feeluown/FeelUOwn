from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QComboBox, QWidget

from feeluown.models import AlbumType
from feeluown.widgets import TextButton


class SongsTableToolbar(QWidget):
    play_all_needed = pyqtSignal()
    filter_albums_needed = pyqtSignal([list])
    filter_text_changed = pyqtSignal([str])

    def __init__(self, parent=None):
        super().__init__(parent)

        self._tmp_buttons = []

        self.play_all_btn = TextButton('播放全部', self)
        self.play_all_btn.clicked.connect(self.play_all_needed.emit)

        self.play_all_btn.setObjectName('play_all')

        # album filters
        self.filter_albums_combobox = QComboBox(self)
        self.filter_albums_combobox.addItems(['所有专辑', '标准', '单曲与EP', '现场', '合辑'])
        self.filter_albums_combobox.currentIndexChanged.connect(
            self.on_albums_filter_changed)
        # 8 works on macOS, don't know if it works on various Linux DEs
        self.filter_albums_combobox.setMinimumContentsLength(8)
        self.filter_albums_combobox.hide()
        self._setup_ui()

    def albums_mode(self):
        self._before_change_mode()
        self.filter_albums_combobox.show()

    def songs_mode(self):
        self._before_change_mode()
        self.play_all_btn.show()

    def artists_mode(self):
        self._before_change_mode()

    def enter_state_playall_start(self):
        self.play_all_btn.setEnabled(False)
        # currently, this is called only when feeluown is fetching songs,
        # so when we enter state_playall_start, we set play all btn text
        # to this.
        self.play_all_btn.setText('获取所有歌曲...')

    def enter_state_playall_end(self):
        self.play_all_btn.setText('获取所有歌曲...done')
        self.play_all_btn.setEnabled(True)
        self.play_all_btn.setText('播放全部')

    def add_tmp_button(self, button):
        """Append text button"""
        if button not in self._tmp_buttons:
            # FIXME(cosven): the button inserted isn't aligned with other buttons
            self._layout.insertWidget(len(self._tmp_buttons) + 1, button)
            self._tmp_buttons.append(button)

    def _setup_ui(self):
        self._layout = QHBoxLayout(self)
        # left margin of meta widget is 30, we align with it
        # bottom margin of meta widget is 15, we should be larger than that
        self._layout.setContentsMargins(30, 15, 30, 10)
        self._layout.addWidget(self.play_all_btn)
        self._layout.addStretch(0)
        self._layout.addWidget(self.filter_albums_combobox)

    def _before_change_mode(self):
        """filter all filter buttons"""
        for button in self._tmp_buttons:
            self._layout.removeWidget(button)
            button.close()
        self._tmp_buttons.clear()
        self.filter_albums_combobox.hide()
        self.play_all_btn.hide()

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
