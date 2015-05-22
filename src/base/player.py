# -*- coding: utf8 -*-

from PyQt5.QtMultimedia import *


class Player(QMediaPlayer):
    """allows the playing of a media source

    The Ui interact with the player with specification.
    make each Mediacontent correspond to a certain music model data
    """
    def __init__(self, parent=None):
        super(Player, self).__init(parent)
        self.__music_list = list()
        self.current_
        self.__repeat = 2     # 2 for all, 1 for one, 0 for false
        self.__shuffle = False