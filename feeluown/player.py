# -*- coding:utf8 -*-

import random
import asyncio

import requests

from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMessageBox

from .utils import singleton, show_requests_progress
from .logger import LOG


@singleton
class Player(QMediaPlayer):
    signal_download_progress = pyqtSignal([int])

    signal_player_media_changed = pyqtSignal([dict])
    signal_playlist_is_empty = pyqtSignal()
    signal_playback_mode_changed = pyqtSignal([int])
    signal_playlist_finished = pyqtSignal()

    signal_song_required = pyqtSignal()
    finished = pyqtSignal()

    _music_list = list()    # 里面的对象是music_model
    _current_index = 0
    playback_mode = 3
    last_playback_mode = 3
    _other_mode = False

    def __init__(self, parent=None):
        super().__init__(parent)

        self.error.connect(self.on_error_occured)
        self.mediaChanged.connect(self.on_media_changed)
        self.mediaStatusChanged.connect(self.on_media_status_changed)

        self._app_event_loop = asyncio.get_event_loop()
        self._music_error_times = 0

        # latency of retying next operation when error happened
        self._retry_latency = 3
        # when _music_error_times reached _music_error_maximum, play next music
        self._music_error_maximum = 3

    def change_player_mode_to_normal(self):
        LOG.info('退出特殊的播放模式')
        self._other_mode = False
        self.set_play_mode(self.last_playback_mode)

    def change_player_mode_to_other(self):
        # player mode: such as fm mode, different from playback mode
        LOG.info('进入特殊的播放模式')
        self._other_mode = True
        self.set_play_mode(2)

    def _record_playback_mode(self):
        self.last_playback_mode = self.playback_mode

    @pyqtSlot(QMediaContent)
    def on_media_changed(self, media_content):
        music_model = self._music_list[self._current_index]
        self.signal_player_media_changed.emit(music_model)

    @pyqtSlot(QMediaPlayer.MediaStatus)
    def on_media_status_changed(self, state):
        if state == QMediaPlayer.EndOfMedia:
            self.finished.emit()
            self.stop()
            if (self._current_index == len(self._music_list) - 1) and\
                    self._other_mode:
                self.signal_playlist_finished.emit()
                LOG.info("播放列表播放完毕")
            if not self._other_mode:
                self.play_next()
        # TODO: at hotkey linux module, when it call
        #       Controller.player.play_next or last may stop the player
        #       add following code to fix the problem.
        elif state in (QMediaPlayer.LoadedMedia, ):
            self.play()

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
        if url.startswith('http'):
            media_content = QMediaContent(QUrl(url))
        else:
            media_content = QMediaContent(QUrl.fromLocalFile(url))
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
            if index == 0 and self._other_mode:
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
        if error == QMediaPlayer.FormatError or\
                error == QMediaPlayer.ServiceMissingError:
            m = QMessageBox(
                QMessageBox.Warning,
                u"错误提示",
                "第一次运行出现该错误可能是由于缺少解码器，"
                "请参考项目主页 https://github.com/cosven/FeelUOwn 。"
                "\n 也可能是网络已经断开，请检查您的网络连接",
                QMessageBox.Yes | QMessageBox.No)
            if m.exec() == QMessageBox.Yes:
                QApplication.quit()
            else:
                LOG.error(u'播放器出现error, 类型为' + str(error))
        if error == QMediaPlayer.NetworkError:
            if self._music_error_times >= self._music_error_maximum or \
                    self._current_index < 0 or\
                    self._current_index >= len(self._music_list):
                self._music_error_times = 0
                self._app_event_loop.call_later(
                    self._retry_latency, self.play_next)
                LOG.error(
                    u'播放器出现错误：网络连接失败，{}秒后尝试播放下一首'.
                    format(self._retry_latency))
            else:
                self._music_error_times += 1
                self._app_event_loop.call_later(
                    self._retry_latency,
                    self.play, self._music_list[self._current_index])
                LOG.error(u'播放器出现错误：网络连接失败, {}秒后重试'.
                          format(self._retry_latency))
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

    def save_song(self, song_model, filepath):
        res = requests.get(song_model['url'], stream=True)
        if res.status_code == 200:
            print('status code 200')
            content = show_requests_progress(
                    res, self.signal_download_progress)
            with open(filepath, 'wb') as f:
                f.write(content)
                LOG.info("save song %s successful" % song_model['name'])
                return True
        LOG.info("save song %s failed" % song_model['name'])
        return False

    def set_play_mode(self, mode=4):
        # item once: 0
        # item in loop: 1
        # sequential: 2
        # loop: 3
        # random: 4
        self._record_playback_mode()
        self.playback_mode = mode
        self.signal_playback_mode_changed.emit(mode)
