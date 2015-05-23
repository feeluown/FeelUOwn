# -*- coding:utf8 -*-

from PyQt5.QtMultimedia import *

from src.base.common import singleton
from src.base.logger import LOG

@singleton
class Player(QMediaPlayer):
    """allows the playing of a media source

    The Ui interact with the player with specification.
    make each Mediacontent correspond to a certain music model data
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__music_list = list()
        self.__cache_list = dict()      # key:music_id, value: mediacontent
        self.__current_playing_index = 0      # curreent playing music's index in __music_list
        self.repeat = 2     # 2 for all, 1 for one, 0 for false
        self.shuffle = False    #

    def append_music(self, music_model):
        pass

    def remove_music(self, music_id):
        pass

    def cache_music(self, music_index):
        pass

    def set_music_list(self, music_list):
        pass

    def set_current_playing_index(self):
        return


if __name__ == "__main__":
    p1 = Player()
    p2 = Player()
    print(id(p1), id(p2))   # to check singleton