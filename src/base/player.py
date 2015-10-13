# -*- coding:utf8 -*-

import random
import asyncio

from PyQt5.QtMultimedia import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from base.utils import singleton
from base.logger import LOG


@singleton
class Player(QMediaPlayer):
    signal_player_media_changed = pyqtSignal([dict])
    signal_playlist_is_empty = pyqtSignal()
    signal_playback_mode_changed = pyqtSignal([int])
    signal_playlist_finished = pyqtSignal()     # only for playback_mode 2

    signal_song_required = pyqtSignal()
    finished = pyqtSignal()

    _music_list = list()    # 里面的对象是music_model
    _current_index = 0
    playback_mode = 3
    _fm_mode = False

    def __init__(self, parent=None):
        super().__init__(parent)

        self.error.connect(self.on_error_occured)
        self.mediaChanged.connect(self.on_media_changed)
        self.mediaStatusChanged.connect(self.on_media_status_changed)

        self._app_event_loop = asyncio.get_event_loop()

    def change_player_mode(self):
        """fm 和 正常两种模式切换"""
        self._fm_mode = ~self._fm_mode
        self.playback_mode = 2 if self._fm_mode else 4
        self.signal_playback_mode_changed.emit(self.playback_mode)

    @pyqtSlot(QMediaContent)
    def on_media_changed(self, media_content):
        music_model = self._music_list[self._current_index]
        self.signal_player_media_changed.emit(music_model)

    @pyqtSlot(QMediaPlayer.MediaStatus)
    def on_media_status_changed(self, state):
        if state == QMediaPlayer.EndOfMedia:
            self.finished.emit()
            self.stop()
            if self._current_index == len(self._music_list) - 1 and self.playback_mode == 2:
                self.signal_playlist_finished.emit()
                LOG.info("播放列表播放完毕")
            if not self._fm_mode:
                self.play_next()

    def add_music(self, music_model):
        for i, music in enumerate(self._music_list):
            if music_model['id'] == music['id']:
                return False
        self._music_list.append(music_model)
        return True

    def remove_music(self, mid):
        for i, music_model in enumerate(self._music_list):
            if mid == music_model['id']:
                self._music_list.pop(i)
                return True
        return False

    @classmethod
    def get_media_content_from_model(cls, music_model):
        url = music_model['url']
        media_content = QMediaContent(QUrl(url))
        return media_content

    def set_music_list(self, music_list):
        self._music_list = []
        self._music_list = music_list
        if len(self._music_list):
            self.play(self._music_list[0])

    def clear_playlist(self):
        self._music_list = []
        self._current_index = 0
        self.stop()

    def is_music_in_list(self, mid):
        """
        :param mid: 音乐的ID
        :return:
        """
        for music in self._music_list:
            if mid == music['id']:
                return True
        return False

    def play(self, music_model=None):
        """播放一首音乐

        如果music_model 不是None的话，
        就尝试将它加入当前播放列表，加入成功返回True, 否则返回False
        """
        if music_model is None:
            super().play()
            return False

        flag = self.add_music(music_model)

        media_content = self.get_media_content_from_model(music_model)
        self._current_index = self.get_index_by_model(music_model)
        super().stop()
        self.setMedia(media_content)
        super().play()
        return flag

    def get_index_by_model(self, music_model):
        for i, music in enumerate(self._music_list):
            if music_model['id'] == music['id']:
                return i
        return None

    def play_or_pause(self):
        if len(self._music_list) is 0:
            self.signal_playlist_is_empty.emit()
            return
        if self.state() == QMediaPlayer.PlayingState:
            self.pause()
        elif self.state() == QMediaPlayer.PausedState:
            self.play()
        else:
            self.play_next()

    def play_next(self):
        index = self.get_next_song_index()
        if index is not None:
            if index == 0 and self.playback_mode == 2:
                self.signal_playlist_finished.emit()
                LOG.info("播放列表播放完毕")
                return
            music_model = self._music_list[index]
            self._current_index = index
            self.play(music_model)
            return True
        else:
            self.signal_playlist_is_empty.emit()
            return False

    def play_last(self):
        index = self.get_previous_song_index()
        if index is not None:
            music_model = self._music_list[index]
            self._current_index = index
            self.play(music_model)
            return True
        else:
            self.signal_playlist_is_empty.emit()
            return False

    @pyqtSlot(QMediaPlayer.Error)
    def on_error_occured(self, error):
        self.setMedia(QMediaContent())
        self.pause()
        if error == QMediaPlayer.FormatError or error == QMediaPlayer.ServiceMissingError:
            m = QMessageBox(QMessageBox.Warning, u"错误提示", "第一次运行出现该错误可能是由于缺少解码器，请参考项目主页\
            https://github.com/cosven/FeelUOwn 安装依赖。\n 如果不是第一次运行，那就可能是网络已经断开，请检查您的网络连接", QMessageBox.Yes | QMessageBox.No)
            if m.exec() == QMessageBox.Yes:
                QApplication.quit()
            else:
                LOG.error(u'播放器出现error, 类型为' + str(error))
        if error == QMediaPlayer.NetworkError:
            latency = 3
            if self._current_index >= 0 and len(self._music_list) > self._current_index:
                self._app_event_loop.call_later(latency, self.play, self._music_list[self._current_index])
                LOG.error(u'播放器出现错误：网络连接失败, {}秒后重试'.format(latency))
            else:
                LOG.error(u'播放器出现错误：网络连接失败')
        elif error == QMediaPlayer.ResourceError:
            LOG.error(u'播放器出现错误：缺少解码器')
        return

    def get_next_song_index(self):
        if len(self._music_list) is 0:
            return None
        if self.playback_mode == 1:
            return self._current_index
        elif self.playback_mode == 3:
            if self._current_index >= len(self._music_list) - 1:
                return 0
            else:
                return self._current_index + 1
        else:
            return random.choice(range(len(self._music_list)))

    def get_previous_song_index(self):
        if len(self._music_list) is 0:
            return None
        if self.playback_mode == 1:
            return self._current_index
        elif self.playback_mode == 3:
            if self._current_index is 0:
                return len(self._music_list) - 1
            else:
                return self._current_index - 1
        else:
            return random.choice(range(len(self._music_list)))

    @classmethod
    def set_play_mode(cls, mode=4):
        # item once: 0
        # item in loop: 1
        # sequential: 2
        # loop: 3
        # random: 4
        cls.playback_mode = mode

    @classmethod
    def set_play_mode_random(cls):
        classmethod.playback_mode = 4

    @classmethod
    def set_play_mode_loop(cls):
        classmethod.playback_mode = 3

    @classmethod
    def set_play_mode_one_in_loop(cls):
        classmethod.playback_mode = 2

    @pyqtSlot(int)
    def on_playback_mode_changed(self, playback_mode):
        self.set_play_mode(playback_mode)
        self.signal_playback_mode_changed.emit(playback_mode)
