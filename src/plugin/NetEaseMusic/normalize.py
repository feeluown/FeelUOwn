# -*- coding: utf8 -*-

import os
import hashlib, time
import asyncio
import re

from constants import DATA_PATH

from base.logger import LOG
from base.common import singleton, write_json_into_file, func_coroutine
from base.models import MusicModel, UserModel, PlaylistModel, ArtistModel, \
    AlbumModel, BriefPlaylistModel, BriefMusicModel, BriefArtistModel, BriefAlbumModel, \
    AlbumDetailModel, ArtistDetailModel, MvModel, LyricModel
from plugin.NetEaseMusic.api import NetEase

from _thread import start_new_thread


"""
这些函数返回的数据都需要以数据model中的东西为标准。

比如说：
- 返回一个music，那么这个数据必须符合 music model.
"""

def login_required(func):
    def wrapper(*args):
        this = args[0]
        if this.uid == 0:
            return {'code': 401}    # Unauthorized
        func(*args)
    return wrapper


def access_music(music_data):
    """处理从服务获取的原始数据，对它的一些字段进行过滤和改名，返回符合标准的music数据
    :param music_data:
    :return:
    """
    music_data['url'] = music_data['mp3Url']
    song = MusicModel(music_data).get_dict()

    for i, artist in enumerate(song['artists']):
        artist_ = ArtistModel(artist).get_dict()
        song['artists'][i] = artist_

    song['album'] = AlbumModel(song['album']).get_dict()
    return song


def access_brief_music(music_data):

    song = BriefMusicModel(music_data).get_dict()

    for i, artist in enumerate(song['artists']):
        artist = BriefArtistModel(artist).get_dict()
        song['artists'][i] = artist

    song['album'] = BriefAlbumModel(song['album']).get_dict()
    return song


def access_user(user_data):
    user_data['avatar'] = user_data['profile']['avatarUrl']
    user_data['uid'] = user_data['account']['id']
    user_data['username'] = user_data['profile']['nickname']
    user = UserModel(user_data).get_dict()
    return user


def web_cache_playlist(func):
    cache_data = {}

    def cache(this, *args, **kw):
        if len(args) > 1:
            if not args[1]:    # 不使用缓存

                data = func(this, *args, **kw)
                if data['code'] == 200:
                    cache_data[args[0]] = data
        else:
            if args[0] in cache_data:
                LOG.debug('playlist: ' + cache_data[args[0]]['name'] + ' has been cached')
            else:
                cache_data[args[0]] = func(this, *args, **kw)
        return cache_data[args[0]]
    return cache


@singleton
class NetEaseAPI(object):
    """
    根据标准的数据模型将 网易云音乐的数据 进行格式化
    这个类也需要管理一个数据库，这个数据库中缓存过去访问过的歌曲、列表、专辑图片等信息，以减少网络访问
    """

    user_info_filename = "netease_userinfo.json"

    def __init__(self):
        super().__init__()
        self.ne = NetEase()
        self.uid = 0
        self.favorite_pid = 0   # 喜欢列表

    def get_uid(self):
        return self.uid

    def is_data_avaible(self, data):
        if data['code'] == 200:
            return True
        return False

    def check_login_successful(self):
        if self.ne.check_cookies():
            return True
        else:
            return False

    def set_user(self, data):
        self.uid = data['uid']

    def login(self, username, password, phone=False):
        password = password.encode('utf-8')
        password = hashlib.md5(password).hexdigest()
        data = self.ne.login(username, password, phone)
        if not self.is_data_avaible(data):
            return data

        self.uid = data['account']['id']
        data = access_user(data)
        data['code'] = 200
        self.save_user_info(data)
        return data

    def auto_login(self, username, pw_encrypt, phone=False):
        """login into website with username and password which has been ecrypted
        """
        data = self.ne.login(username, pw_encrypt, phone)
        if not self.is_data_avaible(data):
            return data

        self.uid = data['account']['id']
        data = access_user(data)
        data['code'] = 200
        self.save_user_info(data)
        return data

    def get_captcha_url(self, captcha_id):
        return self.ne.get_captcha_url(captcha_id)

    def confirm_captcha(self, captcha_id, text):
        data = self.ne.confirm_captcha(captcha_id, text)
        if not self.is_data_avaible(data):
            return data

        if data['result'] is False:
            return data['result'], data['captchaId']
        else:
            return data['result'], None

    def get_song_detail(self, mid):
        data = self.ne.song_detail(mid)
        if not self.is_data_avaible(data):
            return data

        songs = []
        for each in data['songs']:
            song = access_music(each)
            songs.append(song)
        return songs

    @web_cache_playlist
    def get_playlist_detail(self, pid, cache=True):
        """貌似这个请求会比较慢

        :param pid:
        :return:
        """
        # LOG.info(time.ctime())
        data = self.ne.playlist_detail(pid)     # 当列表内容多的时候，耗时久
        # LOG.info(time.ctime())
        if not self.is_data_avaible(data):
            return data

        data = data['result']

        data['uid'] = data['userId']
        data['type'] = data['specialType']

        for i, track in enumerate(data['tracks']):
            data['tracks'][i] = access_music(track)
        model = PlaylistModel(data).get_dict()
        LOG.debug('Update playlist cache finish: ' + model['name'])
        return model

    # @login_required     # 装饰器，挺好玩(装逼)的一个东西
    def get_user_playlist(self):
        data = self.ne.user_playlist(self.uid)
        if not self.is_data_avaible(data):
            return data

        playlist = data['playlist']
        result_playlist = []
        for i, brief_playlist in enumerate(playlist):
            brief_playlist['uid'] = brief_playlist['userId']
            brief_playlist['type'] = brief_playlist['specialType']

            if brief_playlist['type'] == 5:
                self.favorite_pid = brief_playlist['id']

            result_playlist.append(BriefPlaylistModel(brief_playlist).get_dict())
        return result_playlist

    def search(self, s, stype=1, offset=0, total='true', limit=60):
        data = self.ne.search(s, stype=1, offset=0, total='true', limit=60)
        if not self.is_data_avaible(data):
            return data

        songs = data['result']['songs']
        for i, song in enumerate(songs):
            songs[i] = access_brief_music(song)
        return songs

    def get_artist_detail(self, artist_id):
        data = self.ne.artist_infos(artist_id)
        if not self.is_data_avaible(data):
            return data

        for i, track in enumerate(data['hotSongs']):
            data['hotSongs'][i] = access_music(track)

        for each_key in data['artist']:
            data[each_key] = data['artist'][each_key]

        model = ArtistDetailModel(data).get_dict()
        return model

    def get_album_detail(self, album_id):
        data = self.ne.album_infos(album_id)
        if not self.is_data_avaible(data):
            return data

        album = data['album']
        for i, track in enumerate(album['songs']):
            album['songs'][i] = access_music(track)
        model = AlbumDetailModel(album).get_dict()
        return model

    def is_playlist_mine(self, playlist_model):
        if playlist_model['uid'] == self.uid:
            return True
        return False

    def is_favorite_music(self, mid):
        data = self.get_playlist_detail(self.favorite_pid)
        if not self.is_data_avaible(data):
            return data
        tracks = data['tracks']
        for track in tracks:
            if track['id'] == mid:
                return True
        return False

    def set_music_to_favorite(self, mid, flag):
        data = self.ne.set_music_favorite(mid, flag)
        self.get_playlist_detail(self.favorite_pid, False)
        return data

    def get_mv_detail(self, mvid):
        data = self.ne.get_mv_detail(mvid)
        if not self.is_data_avaible(data):
            return data

        data = data['data']
        brs = sorted(data['brs'].keys(), key=lambda num: int(num))
        data['url_low'] = data['brs'][brs[0]]
        data['url_high'] = data['brs'][brs[-1]]
        if len(brs) >= 2:
            data['url_middle'] = data['brs'][brs[-2]]
        else:
            data['url_middle'] = data['brs'][brs[-1]]
        model = MvModel(data).get_dict()
        return model

    def get_lyric_detail(self, music_id):
        data = self.ne.get_lyric_by_musicid(music_id)
        if not self.is_data_avaible(data):
            return data

        if 'lrc' not in data.keys():
            return None

        re_express = re.compile("\[\d+:\d+\.\d+\]")
        lyric = data['lrc']['lyric']
        lyric_l = re_express.split(lyric)
        data['lyric'] = lyric_l

        time_s = re_express.findall(lyric)
        for i, each in enumerate(time_s):
            m = int(each[1:3]) * 60000
            s = float(each[4:-1]) * 1000
            time_s[i] = int(m + s)
        data['time_sequence'] = list(time_s)
        data['time_sequence'].insert(0, 0)

        if 'tlyric' in data.keys():
            if data['tlyric']['lyric']:
                translate_lyric = data['tlyric']['lyric']
                tlyric_l = re_express.split(translate_lyric)
                data['translate_lyric'] = tlyric_l
            else:
                data['translate_lyric'] = []
        else:
            data['translate_lyric'] = []

        model = LyricModel(data).get_dict()

        return model

    @func_coroutine
    def save_user_info(self, data_dict):
        if write_json_into_file(data_dict, DATA_PATH + self.user_info_filename):
            LOG.info("Save User info successfully")


if __name__ == "__main__":
    api = NetEaseAPI()
    # print(api.get_song_detail(17346999))    # Thank you
    # print(api.get_playlist_detail(16199365))  # 我喜欢的列表
    # print(api.get_user_playlist())    # 我的列表
    print(api.search('linkin park'))
