# -*- coding: utf8 -*-

from base.player import Player
from interfaces import ControllerApi
from widgets.notify import NotifyWidget


class SimilarSongsMode(object):
    """与fm的逻辑基本相同，之后考虑重构
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
                cls.exit_()
                return
            cls._player.set_music_list([music_models[0]])
        else:
            cls._songs = cls._api.get_simi_songs(ControllerApi.state['current_mid'])
            if not ControllerApi.api.is_response_ok(cls._songs):
                cls._player.stop()
                cls._notify.show_message("Error", "网络异常，请检查网络连接")
                cls.exit_()
            else:
                cls.reset_song_list()

    @classmethod
    def load_similar_song(cls):
        ControllerApi.state['similar_song'] = True
        ControllerApi.player.change_player_mode()
        ControllerApi.notify_widget.show_message("Info", "进入单曲电台播放模式")
        cls.load()
        ControllerApi.player.signal_playlist_finished.connect(cls.on_next_music_required)

    @classmethod
    def exit_(cls):
        if ControllerApi.state['similar_song']:
            ControllerApi.player.change_player_mode()
            ControllerApi.notify_widget.show_message("O(∩_∩)O", "退出单曲电台播放模式")
            cls.exit()
            ControllerApi.state['similar_song'] = False

    @classmethod
    def on_next_music_required(cls):
        cls.reset_song_list()

    @classmethod
    def exit(cls):
        cls._player = None
        cls._api = None
        cls._notify = None
