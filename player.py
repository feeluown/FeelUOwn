# -*- coding:utf8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from api import NetEase
from models import DataModel

try:
    from PyQt4.phonon import Phonon
except ImportError:
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "NetEaseMusic-ThirdParty",
            "Your Qt installation does not have Phonon support.",
            QMessageBox.Ok | QMessageBox.Default,
            QMessageBox.NoButton)
    sys.exit(1)


class Player(Phonon.MediaObject):
    def __init__(self, parent=None):
        super(Player, self).__init__(parent)
        self.__music_id = 0
        self.__next_music_id = 0
        self.net_ease = NetEase()
        self.model = DataModel()

    def setCurrentMusicId(self, mid):
        """
        如果歌曲手动切换，一定会调用这个函数
        设置当前的musicid
        """
        source = self.getSourceByMid(mid)
        self.__music_id = mid
        # 下首歌的Id实际上会在About_to_finish函数重新赋值
        # 这里赋值一次是为了保证当前播放的mid和source对应
        self.__next_music_id = mid
        self.stop()
        self.setCurrentSource(source)
        self.play()

    def getCurrentMusicId(self):
        return self.__next_music_id

    def addMusicToPlay(self, mid):
        """
        如果歌曲自然切换，一定会调用这个函数
        enqueue 将要播放的歌曲
        """
        source = self.getSourceByMid(mid)
        self.__next_music_id = mid
        self.enqueue(source)

    def getSourceByMid(self, mid):
        musics = self.net_ease.song_detail(mid)
        datamodel = self.model.music()
        try:
            music_model = self.model.set_datamodel_from_data(musics[0], datamodel)
            source = Phonon.MediaSource(music_model['mp3Url'])
            return source
        except Exception as e:
            print(str(e))
