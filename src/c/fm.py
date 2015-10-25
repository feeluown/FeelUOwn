# -*- coding: utf8 -*-

from base.player import Player
from interfaces import ControllerApi
from widgets.notify import NotifyWidget


class FmMode(object):
    """fm mode 一些说明

    当切换到fm播放模式的时候，每向服务器请求一次，服务器会返回几首歌曲
    所以当这几首歌曲播放结束的时候，我们要向服务器请求下几首歌
    """
    _api = None
    _player = None
    _notify = None
    _songs = []     # brief music model

    @classmethod
    def load(cls):

        cls._notify = NotifyWidget()

        cls._api = ControllerApi.api
        cls._player = Player()
        cls._player.stop()

        cls.reset_song_list()

    @classmethod
    def reset_song_list(cls):
        cls._player.clear_playlist()
        if len(cls._songs) > 0:
            song = cls._songs.pop()
            mid = song['id']
            music_models = cls._api.get_song_detail(mid)
            if not ControllerApi.api.is_response_ok(music_models):
                cls.exit_fm()
                return
            cls._player.set_music_list([music_models[0]])
        else:
            cls._songs = cls._api.get_radio_songs()
            if not ControllerApi.api.is_response_ok(cls._songs):
                cls._player.stop()
                cls._notify.show_message("Error", "网络异常，请检查网络连接")
                cls.exit_fm()
            else:
                cls.reset_song_list()

    @classmethod
    def load_fm(cls):
        """播放FM

        1. webkit加载FM播放页面，可以有点动画和设计
        2. 由于播放FM，要时常向服务器请求歌曲，所以逻辑跟正常播放时有点不一样
        """
        ControllerApi.state['fm'] = True
        ControllerApi.player.change_player_mode()
        ControllerApi.notify_widget.show_message("Info", "进入FM播放模式")
        cls.load()
        ControllerApi.player.signal_playlist_finished.connect(FmMode.on_next_music_required)

    @classmethod
    def exit_fm(cls):
        """如果从webview播放一首歌，就退出fm模式，暂时使用这个逻辑
        """
        if ControllerApi.state['fm']:
            ControllerApi.player.change_player_mode()
            ControllerApi.notify_widget.show_message("O(∩_∩)O", "退出FM播放模式")
            FmMode.exit()
            ControllerApi.state['fm'] = False

    @classmethod
    def on_next_music_required(cls):
        cls.reset_song_list()

    @classmethod
    def exit(cls):
        cls._player = None
        cls._api = None
        cls._notify = None
