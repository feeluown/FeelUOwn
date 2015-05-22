# -*- coding:utf8 -*-

from PyQt5.QtMultimedia import *

from src.base.common import singleton


@singleton
class Player(QMediaPlayer):
    """allows the playing of a media source

    The Ui interact with the player with specification.
    make each Mediacontent correspond to a certain music model data
    """
    def __init__(self, parent=None):
        super(Player, self).__init(parent)
        self.__music_list = list()
        self.current_playing_index = 0      # curreent playing music's index in __music_list
        self.__repeat = 2     # 2 for all, 1 for one, 0 for false
        self.__shuffle = False