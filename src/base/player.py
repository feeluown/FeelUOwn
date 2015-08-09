# -*- coding:utf8 -*-

from PyQt5.QtMultimedia import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from base.common import singleton
from base.logger import LOG


@singleton
class Player(QMediaPlayer):
    """allows the playing of a media source

    The Ui interact with the player with specification.
    make each Mediacontent correspond to a certain music model data

    它也需要维护一个 已下载歌曲的数据库，防止重复下载或者缓存歌曲（暂时这样）
    """

    signal_player_media_changed = pyqtSignal([dict], [QMediaContent])
    signal_playlist_is_empty = pyqtSignal()
    signal_playback_mode_changed = pyqtSignal([QMediaPlaylist.PlaybackMode])
    signal_player_error = pyqtSignal([str])

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__music_list = list()      # 和播放列表同步，保存歌曲名，歌手等信息。（里面的对象是music_model）
        self.__cache_list = list()      # {id:music_id, content: media_content}
        self.__playlist = QMediaPlaylist()  # 播放列表。里面的对象是qmediacontent

        self.setPlaylist(self.__playlist)

        self.init()

    def init(self):
        self.set_play_mode()
        self.init_signal_binding()

    def init_signal_binding(self):
        self.__playlist.currentIndexChanged.connect(self.on_current_index_changed)
        self.__playlist.playbackModeChanged.connect(self.on_playback_mode_changed)
        self.error.connect(self.on_error_occured)

    def set_play_mode(self, mode=3):
        # item once: 0
        # item in loop: 1
        # sequential: 2
        # loop: 3
        # random: 4
        self.__playlist.setPlaybackMode(mode)

    def add_music(self, music_model):
        """向当前播放列表中添加一首音乐

        1. 如果这首音乐已经存在于列表当中，返回Fasle 和 index.(添加失败)
        2. 如果不存在，返回True 和 index=length-1.(添加成功)

        这个函数保证了当前播放列表的歌曲不会重复

        :param music_model:
        :return:
        """
        for i, music in enumerate(self.__music_list):
            if music_model['id'] == music['id']:
                return False, i
        self.__music_list.append(music_model)
        media_content = self.get_media_content_from_model(music_model)
        self.__playlist.addMedia(media_content)
        length = len(self.__music_list)
        index = length - 1
        return True, index

    def remove_music(self, mid):
        for i, music_model in enumerate(self.__music_list):
            if mid == music_model['id']:
                if self.__playlist.currentIndex() == i:
                    self.__playlist.removeMedia(i)
                    self.__music_list.pop(i)
                    LOG.info(u'移除当前正在播放的歌曲')
                    self.__playlist.next()
                    break
                self.__playlist.removeMedia(i)
                self.__music_list.pop(i)
                break

        for cache in self.__cache_list:
            if mid == cache['id']:
                self.__cache_list.remove(cache)
                return True

    def get_media_content_from_model(self, music_model):
        # if music_model['id'] in downloaded
        mid = music_model['id']

        # 判断之前是否播放过，是否已经缓存下来，以后需要改变缓存的算法
        for i, each in enumerate(self.__cache_list):
            if mid == each['id']:
                LOG.info(music_model['name'] + ' has been cached')
                return self.__cache_list[i]['content']

        return self.cache_music(music_model)

    def cache_music(self, music_model):
        url = music_model['url']
        media_content = QMediaContent(QUrl(url))
        cache = dict()
        cache['id'] = music_model['id']
        cache['content'] = media_content
        self.__cache_list.append(cache)
        return media_content

    def set_music_list(self, music_list):
        self.__music_list = []
        self.__playlist.clear()
        self.play(music_list[0])
        for music in music_list:
            self.add_music(music)

    def is_music_in_list(self, mid):
        """
        :param mid: 音乐的ID
        :return:
        """
        for music in self.__music_list:
            if mid == music['id']:
                return True
        return False

    def play(self, music_model=None):
        """播放一首音乐
        1. 如果music_model 不是None的话，就尝试将它加入当前播放列表，加入成功返回True, 否则返回False
        :param music_model:
        :return:
        """
        if music_model is None:
            super().play()
            return False

        # 播放一首特定的音乐
        flag, index = self.add_music(music_model)

        super().stop()
        self.__playlist.setCurrentIndex(index)
        super().play()
        return flag

    def when_playlist_empty(func):
        def wrapper(self, *args, **kwargs):
            if self.__playlist.isEmpty():
                self.signal_playlist_is_empty.emit()
                return 
            return func(self, *args, **kwargs)
        return wrapper

    def set_play_mode_random(self):
        self.__playlist.setPlaybackMode(4)

    def set_play_mode_loop(self):
        self.__playlist.setPlaybackMode(3)

    def set_play_mode_one_in_loop(self):
        self.__playlist.setPlaybackMode(1)

    @when_playlist_empty
    def play_or_pause(self, flag=True):
        if self.state() == QMediaPlayer.PlayingState:
            self.pause()
        elif self.state() == QMediaPlayer.PausedState:
            self.play()
        else:
            pass

    @when_playlist_empty
    @pyqtSlot()
    def play_next(self, flag=True):
        # self.stop()
        self.__playlist.next()
        # self.play()

    @when_playlist_empty
    @pyqtSlot()
    def play_last(self, flag=True):
        self.__playlist.previous()

    @pyqtSlot(int)
    def on_current_index_changed(self, index):
        music_model = self.__music_list[index]
        self.signal_player_media_changed.emit(music_model)

    @pyqtSlot(QMediaPlayer.Error)
    def on_error_occured(self, error):
        self.pause()
        if error == 2 or error == 5:
            m = QMessageBox(QMessageBox.Warning, u"错误提示", "第一次运行出现该错误可能是由于缺少解码器，请参考项目主页\
            https://github.com/cosven/FeelUOwn 安装依赖。\n 如果不是第一次运行，那就可能是网络已经断开，请检查您的网络连接", QMessageBox.Yes | QMessageBox.No)
            if m.exec() == QMessageBox.Yes:
                QApplication.quit()
            else:
                LOG.error(u'播放器出现error, 类型为' + str(error))
        if error == 3 or error == 1:
            LOG.error(u'播放器出现错误。可能是网络连接失败，也有可能缺少解码器')
        return

    @pyqtSlot(QMediaPlaylist.PlaybackMode)
    def on_playback_mode_changed(self, playback_mode):
        self.signal_playback_mode_changed.emit(playback_mode)
