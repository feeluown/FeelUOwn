# -*- coding: utf8 -*-

from controller_api import ControllerApi

from widgets.playlist_widget import PlaylistItem


class ModeBase(object):
    _songs = []     # brief music model

    @classmethod
    def get_songs(cls):
        return []

    @classmethod
    def load(cls):
        pass

    @classmethod
    def reset_song_list(cls):
        ControllerApi.player.clear_playlist()
        if len(cls._songs) > 0:
            song = cls._songs.pop()
            mid = song['id']
            music_model = ControllerApi.api.get_song_detail(mid)
            if not ControllerApi.api.is_response_ok(music_model):
                cls.exit_()
                return
            ControllerApi.player.set_music_list([music_model])
        else:
            cls._songs = cls.get_songs()
            if not ControllerApi.api.is_response_ok(cls._songs):
                ControllerApi.player.stop()
                ControllerApi.notify_widget.show_message("Error", "网络异常，请检查网络连接")
                cls.exit_()
            elif cls._songs == []:
                ControllerApi.notify_widget.show_message("|--|", "未知错误")
                cls.exit_()
            else:
                cls.reset_song_list()

    @classmethod
    def load_(cls):
        cls._songs = []  # reinit songs list
        ControllerApi.player.signal_playlist_finished.connect(cls.on_next_music_required)
        print(cls, "connect")
        cls.load()

    @classmethod
    def exit_(cls):
        ControllerApi.player.signal_playlist_finished.disconnect(cls.on_next_music_required)
        print(cls, "disconnect")
        cls._songs = []
        cls.exit()

    @classmethod
    def on_next_music_required(cls):
        cls.reset_song_list()

    @classmethod
    def exit(cls):
        pass


class FmMode(ModeBase):

    @classmethod
    def load(cls):
        ControllerApi.notify_widget.show_message("通知", "进入 FM 播放模式")
        ControllerApi.player.stop()
        cls.reset_song_list()

    @classmethod
    def exit(cls):
        ControllerApi.notify_widget.show_message("通知", "退出 FM 播放模式")

    @classmethod
    def get_songs(cls):
        songs = ControllerApi.api.get_radio_songs()
        return songs if songs else []


class SimiSongsMode(ModeBase):

    @classmethod
    def load(cls):
        ControllerApi.notify_widget.show_message("通知", "您已成功进入单曲电台\n接下来的歌曲将和这首歌风格类似")
        ControllerApi.player.stop()
        cls.reset_song_list()

    @classmethod
    def exit(cls):
        ControllerApi.notify_widget.show_message("通知", "退出单曲电台播放模式")

    @classmethod
    def get_songs(cls):
        if ControllerApi.state['current_mid'] == 0:
            ControllerApi.notify_widget.show_message("O.o", "无法寻找相似歌曲")
            return []
        songs = ControllerApi.api.get_simi_songs(ControllerApi.state['current_mid'])
        return songs if songs else []


class ModesManger(object):
    def __init__(self):
        super().__init__()
        self.current_mode = 0   # 0 normal, 1 fm, 2 simi

    def change_to_normal(self):
        if self.current_mode == 1:
            FmMode.exit_()
        elif self.current_mode == 2:
            SimiSongsMode.exit_()
        ControllerApi.player.change_player_mode_to_normal()
        self.current_mode = 0

    def change_to_fm(self):
        if self.current_mode == 2:
            SimiSongsMode.exit_()
        elif self.current_mode == 1:
            ControllerApi.notify_widget.show_message("提示", "你正处于FM模式")
            return
        self.current_mode = 1
        ControllerApi.player.change_player_mode_to_other()
        FmMode.load_()

    def change_to_simi(self):
        PlaylistItem.de_active_all()
        if self.current_mode == 1:
            FmMode.exit_()
        elif self.current_mode == 2:
            ControllerApi.notify_widget.show_message("提示", "你正处于单曲电台模式")
            return
        self.current_mode = 2
        ControllerApi.player.change_player_mode_to_other()
        SimiSongsMode.load_()
