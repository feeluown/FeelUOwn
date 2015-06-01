# -*- coding:utf8 -*-

from PyQt5.QtMultimedia import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from base.common import singleton
from base.logger import LOG
import setting


@singleton
class Player(QMediaPlayer):
    """allows the playing of a media source

    The Ui interact with the player with specification.
    make each Mediacontent correspond to a certain music model data

    它也需要维护一个 已下载歌曲的数据库，防止重复下载或者缓存歌曲（暂时这样）
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__music_list = list()      # music_model object list
        self.__cache_list = dict()      # key:music_id, value: mediacontent
        self.__current_playing_index = 0      # curreent playing music's index in __music_list
        self.__playlist = QMediaPlaylist()

        self.setPlaylist(self.__playlist)

        self.bufferStatusChanged.connect(self.debug)
        self.mediaStatusChanged.connect(self.debug)
        self.audioAvailableChanged.connect(self.debug)

        self.init()

    def init(self):
        self.set_play_mode()

    def set_play_mode(self, mode=3):
        # item once: 0
        # item in loop: 1
        # sequential: 2
        # loop: 3
        # random: 4
        self.__playlist.setPlaybackMode(mode)

    def add_music(self, music_model):
        self.__music_list.append(music_model)
        media_content = self.get_media_content_from_model(music_model)
        self.__playlist.addMedia(media_content)

    def remove_music(self, music_id):
        for i, music_model in enumerate(self.__music_list):
            if music_id in music_model['id']:
                self.__music_list.remove(music_model)
                return self.__playlist.removeMedia(i)
            else:
                return False

    def get_media_content_from_model(self, music_model):
        # if music_model['id'] in downloaded
        url = music_model['url']
        media_content = QMediaContent(QUrl(url))
        return media_content

    def cache_music(self, music_index):
        music_model = self.__music_list[music_index]
        # if mid in downloaded
        media_content = self.get_media_content_from_model(music_model)
        return media_content

    def set_music_list(self, music_list):
        self.__music_list = music_list

    def set_current_playing_index(self, index):
        self.__current_playing_index = index
        self.__playlist.setCurrentIndex(index)


    def play(self, index=None):
        if index is None:
            super().play()
            return
        self.set_current_playing_index(index)
        self.play()

    def debug(self, p):
        print(p)



if __name__ == "__main__":
    import sys
    from base.models import MusicModel

    app = QApplication(sys.argv)
    w = QWidget()
    
    p = Player()

    url = 'http://m1.music.126.net/ci1d94nRmgrWaF4IxpZXLQ==/2022001883489851.mp3'  # way back into love
    url = 'http://m1.music.126.net/Gybpf5bX9zfNesjXxZl3qw==/2053887720715417.mp3'  # secret base
    url = 'http://m1.music.126.net/3wDUT2VE7NLeb8ceq9ejFA==/1164382813825096.mp3'

    data = {
        'id': 1234,
        'name': 'secret base',
        'artists': ['unknown'],
        'album': {'name': 'test'},
        'duration': 2000,
        'url': url
    }
    music_model1 = MusicModel(data)
    p.add_music(music_model1)

    url = 'http://m1.music.126.net/ci1d94nRmgrWaF4IxpZXLQ==/2022001883489851.mp3'  # way back into love
    data = {
        'id': 1234,
        'name': 'secret base',
        'artists': ['unknown'],
        'album': {'name': 'test'},
        'duration': 2000,
        'url': url
    }
    music_model2 = MusicModel(data)
    p.add_music(music_model2)

    p.play()
    
    w.show()
    sys.exit(app.exec_())
