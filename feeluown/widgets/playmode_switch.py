# -*- coding:utf8 -*-

from PyQt5.QtMultimedia import QMediaPlaylist
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QLabel

from feeluown.player import Player
from feeluown.logger import LOG
from feeluown.constants import ICON_PATH


# item once: 0
# item in loop: 1
# sequential: 2
# loop: 3
# random: 4
# playmodes = ((1, 'single_repeat.png'), (3, 'repeat.png'), (4, 'random.png'))


class PlaymodeSwitchLabel(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.player = Player()
        self.resize(15, 15)
        self._current_mode = self.player.playback_mode
        self._update_mode_icon()

    def _update_mode_icon(self):
        if self._current_mode == 1:
            self.setPixmap(QPixmap(ICON_PATH + "single_repeat.png").scaled(self.size()))
        elif self._current_mode == 3:
            self.setPixmap(QPixmap(ICON_PATH + "repeat.png").scaled(self.size()))
        elif self._current_mode == 4:
            self.setPixmap(QPixmap(ICON_PATH + "random.png").scaled(self.size()))

    def _switch_mode(self):
        if self._current_mode == 4:
            self._current_mode = 1
        elif self._current_mode == 1:
            self._current_mode = 3
        elif self._current_mode == 3:
            self._current_mode = 4
        else:
            self._current_mode = 4
        self._update_mode_icon()
        self.player.set_play_mode(self._current_mode)

    @pyqtSlot(int)
    def on_mode_changed(self, mode):
        LOG.info('current play mode is %d.'
                 ' 1 for single in loop, 3 for loop, 4 for random' % mode)
        if mode != self._current_mode:
            self._current_mode = mode
            self._switch_mode()

    def mousePressEvent(self, event):
        self._switch_mode()
