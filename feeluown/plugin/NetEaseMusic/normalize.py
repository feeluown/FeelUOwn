# -*- coding: utf8 -*-

import asyncio
import hashlib
import pickle
import re
from functools import partial

from feeluown.logger import LOG
from feeluown.utils import singleton
from feeluown.models import MusicModel, UserModel, PlaylistModel, ArtistModel, \
    AlbumModel, BriefPlaylistModel, BriefMusicModel, BriefArtistModel, BriefAlbumModel, \
    AlbumDetailModel, ArtistDetailModel, MvModel, LyricModel

from .api import NetEase
from .model import PlaylistDb, SongDb, UserDb


"""
这些函数返回的数据都需要以数据model中的东西为标准。

比如说：
- 返回一个music，那么这个数据必须符合 music model.
"""


@singleton
class NetEaseAPI(object):
    """
    根据标准的数据模型将 网易云音乐的数据 进行格式化
    这个类也需要管理一个数据库，这个数据库中缓存过去访问过的\
    歌曲、列表、专辑图片等信息，以减少网络访问
    """

    def __init__(self):
        super().__init__()

        self.headers = {
            'Host': 'music.163.com',
            'Connection': 'keep-alive',
            # 'Content-Type': "application/json; charset=UTF-8",
            'Referer': 'http://music.163.com/',
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2)"
                          " AppleWebKit/537.36 (KHTML, like Gecko)"
                          " Chrome/33.0.1750.152 Safari/537.36"
        }
        self.cookies = dict(appver="1.2.1", os="osx")
        self.uid = 0
        self.favorite_pid = 0   # 喜欢列表

        self.ne = NetEase(self.headers, self.cookies)

    def set_uid(self, uid):
        """uid will be set until login successful"""
        self.uid = uid

    def get_uid(self):
        return self.uid

    def save_user_pw(self, username, password):
        user = UserDb.get_user(self.uid)
        if user is not None:
            user.update(username=username, password=password)
        LOG.info('Save user\'s username and password ')

    def save_cookies(self):
        user = UserDb.get_user(self.uid)
        user.update(_cookies=pickle.dumps(self.ne.cookies))
        LOG.info('Save user cookies')

    def save_login_time(self):
        user = UserDb.get_user(self.uid)
        user.record_login_time()
        LOG.info('Save user login time')

    def login_by_cookies(self):
        if self.ne.check_cookies():
            self._on_login_success()
            return True
        else:
            return False

    def login(self, username, password, phone=False):
        password = password.encode('utf-8')
        password = hashlib.md5(password).hexdigest()
        data = self.ne.login(username, password, phone)
        if not self.is_response_avaible(data):
            return data

        self.set_uid(data['account']['id'])
        data = self.access_data_user(data)
        UserDb.create_or_update(self.uid, pickle.dumps(data))
        self._on_login_success()
        return data

    def auto_login(self, username, pw_encrypt, phone=False):
        """login into website with username and password which has been ecrypted
        """
        data = self.ne.login(username, pw_encrypt, phone)
        if not self.is_response_avaible(data):
            return data

        self.set_uid(data['account']['id'])
        data = self.access_data_user(data)
        user = UserDb.get_user(self.uid)
        user.update(_basic_info=pickle.dumps(data))
        self._on_login_success()
        return data

    def _on_login_success(self):
        self.save_cookies()
        self.save_login_time()

    def get_captcha_url(self, captcha_id):
        return self.ne.get_captcha_url(captcha_id)

    def confirm_captcha(self, captcha_id, text):
        data = self.ne.confirm_captcha(captcha_id, text)
        if not self.is_response_avaible(data):
            return data

        if data['result'] is False:
            return data['result'], data['captchaId']
        else:
            return data['result'], None

    def get_song_detail(self, mid):
        if SongDb.exists(mid):
            # LOG.info("Read song %d from sqlite" % mid)
            return SongDb.get_data(mid)

        data = self.ne.song_detail(mid)
        if not self.is_response_avaible(data):
            return data
        songs = []
        for each in data['songs']:
            song = self.access_music(each)
            songs.append(song)
        model = songs[0]

        song = SongDb(mid=mid, _data=pickle.dumps(model))
        song.save()
        # LOG.info('Save music %d info into sqlite' % mid)

        return model

    def update_playlist_detail(self, pid, data=None):
        data = self.ne.playlist_detail(pid) if data is None else data
        if not self.is_response_avaible(data):
            return data

        data = data['result']
        data['uid'] = data['userId']
        data['type'] = data['specialType']
        for i, track in enumerate(data['tracks']):
            data['tracks'][i] = self.access_music(track)
        model = PlaylistModel(data).get_dict()

        if PlaylistDb.exists(pid):
            PlaylistDb.update_data(pid, model)
        else:
            playlist = PlaylistDb(pid=pid, _data=pickle.dumps(model))
            playlist.save()

        # LOG.info('Save playlist %d info to sqlite' % pid)
        return model

    # TODO: change param 'cache' name to others
    def get_playlist_detail(self, pid, cache=True):
        '''update playlist detail in sqlite if cache is false'''

        if PlaylistDb.exists(pid):
            if cache is False:
                app_event_loop = asyncio.get_event_loop()
                app_event_loop.run_in_executor(
                    None, partial(self.update_playlist_detail, pid))

            # LOG.info("Read playlist %d info from sqlite" % (pid))
            return PlaylistDb.get_data(pid)
        else:
            return self.update_playlist_detail(pid)

    def get_user_playlist(self):
        user = UserDb.get_user(self.uid)
        if user.playlists is not None:
            self._set_favorite_pid(user.playlists)
            app_event_loop = asyncio.get_event_loop()
            app_event_loop.run_in_executor(
                None, partial(self.update_user_playlists))
            return user.playlists
        else:
            return self.update_user_playlists()

    def update_user_playlists(self):
        user = UserDb.get_user(self.uid)
        data = self.ne.user_playlist(self.uid)
        if not self.is_response_avaible(data):
            return data

        playlist = data['playlist']
        result_playlists = []
        for i, brief_playlist in enumerate(playlist):
            brief_playlist['uid'] = brief_playlist['userId']
            brief_playlist['type'] = brief_playlist['specialType']
            result_playlists.append(
                BriefPlaylistModel(brief_playlist).get_dict())
        self._set_favorite_pid(result_playlists)
        LOG.info('update user playlists info')
        user.update(_playlists=pickle.dumps(result_playlists))
        return result_playlists

    def _set_favorite_pid(self, playlists):
        for playlist in playlists:
            if playlist['type'] == 5:
                self.favorite_pid = playlist['id']
                break
        return True

    def search(self, s, stype=1, offset=0, total='true', limit=60):
        data = self.ne.search(s, stype=1, offset=0, total='true', limit=60)
        if not self.is_response_avaible(data):
            return data
        if data['result']['songCount']:
            songs = data['result']['songs']
            for i, song in enumerate(songs):
                songs[i] = self.access_music_brief(song)
            return songs
        else:
            return []

    def get_artist_detail(self, artist_id):
        data = self.ne.artist_infos(artist_id)
        if not self.is_response_avaible(data):
            return data

        for i, track in enumerate(data['hotSongs']):
            data['hotSongs'][i] = self.access_music(track)

        for each_key in data['artist']:
            data[each_key] = data['artist'][each_key]

        model = ArtistDetailModel(data).get_dict()
        return model

    def get_album_detail(self, album_id):
        data = self.ne.album_infos(album_id)
        if not self.is_response_avaible(data):
            return data

        album = data['album']
        for i, track in enumerate(album['songs']):
            album['songs'][i] = self.access_music(track)
        model = AlbumDetailModel(album).get_dict()
        return model

    def is_playlist_mine(self, playlist_model):
        if playlist_model['uid'] == self.uid:
            return True
        return False

    def is_favorite_music(self, mid):
        data = self.get_playlist_detail(self.favorite_pid)
        if not self.is_response_avaible(data):
            return data
        tracks = data['tracks']
        for track in tracks:
            if track['id'] == mid:
                return True
        return False

    def is_favorite_playlist(self, playlist_model):
        if playlist_model['id'] == self.favorite_pid:
            return True
        return False

    def set_music_to_favorite(self, mid, flag):
        data = self.ne.set_music_favorite(mid, flag)
        return data

    def add_song_to_playlist(self, mid, pid):
        data = self.ne.add_music_to_playlist(mid, pid, 'add')
        if not self.is_response_avaible(data):
            return False
        return True

    def get_mv_detail(self, mvid):
        data = self.ne.get_mv_detail(mvid)
        if not self.is_response_avaible(data):
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
        if not self.is_response_avaible(data):
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

    def get_radio_songs(self):
        data = self.ne.get_radio_music()
        if not self.is_response_avaible(data):
            return data
        songs = data['data']
        for i, song in enumerate(songs):
            songs[i] = self.access_music_brief(song)
        return songs

    def get_simi_songs(self, mid, offset=0, limit=10):
        data = self.ne.get_similar_song(mid, offset, limit)
        if not self.is_response_avaible(data):
            return data
        songs = data['songs']
        for i, song in enumerate(songs):
            songs[i] = self.access_music(song)
        return songs

    def get_recommend_songs(self):
        data = self.ne.get_recommend_songs()
        if not self.is_response_avaible(data):
            return data
        songs = data['recommend']
        for i, song in enumerate(songs):
            songs[i] = self.access_music_brief(song)
        return songs

    def update_playlist_name(self, pid, name):
        data = self.ne.update_playlist_name(pid, name)
        if not self.is_response_avaible(data):
            return False
        return True

    def new_playlist(self, name):
        data = self.ne.new_playlist(self.uid, name)
        if not self.is_response_avaible(data):
            return None
        playlist = data['playlist']
        playlist['uid'] = playlist['userId']
        playlist['tracks'] = []
        playlist['type'] = playlist['adType']
        playlist_model = PlaylistModel(playlist)
        return playlist_model

    def delete_playlist(self, pid):
        data = self.ne.delete_playlist(pid)
        if not self.is_response_avaible(data):
            return False
        return True

    @staticmethod
    def access_music(music_data):
        """处理从服务获取的原始数据，对它的一些字段进行过滤和改名，返回符合标准的music数据

        :param music_data:
        :return:
        """
        music_data['url'] = music_data['mp3Url']
        song = MusicModel(music_data).get_dict()

        for i, artist in enumerate(music_data['artists']):
            artist_ = ArtistModel(artist).get_dict()
            song['artists'][i] = artist_

        song['album'] = AlbumModel(music_data['album']).get_dict()
        return song

    @staticmethod
    def access_music_brief(music_data):

        song = BriefMusicModel(music_data).get_dict()

        for i, artist in enumerate(song['artists']):
            artist = BriefArtistModel(artist).get_dict()
            song['artists'][i] = artist

        song['album'] = BriefAlbumModel(song['album']).get_dict()
        return song

    @staticmethod
    def access_data_user(user_data):
        user_data['avatar'] = user_data['profile']['avatarUrl']
        user_data['uid'] = user_data['account']['id']
        user_data['username'] = user_data['profile']['nickname']
        user = UserModel(user_data).get_dict()
        user['code'] = 200
        return user

    @staticmethod
    def is_response_avaible(data):
        """判断api返回的数据是否可用

        TODO: 应该写成一个decorator
        """
        if data is None:
            return False
        if data['code'] == 200:
            return True
        return False

    @staticmethod
    def is_response_ok(data):
        """check response status code"""
        if data is None:
            return False
        if not isinstance(data, dict):
            return True
        if data['code'] == 200:
            return True
        return False


if __name__ == "__main__":
    api = NetEaseAPI()
    # print(api.get_song_detail(17346999))    # Thank you
    # print(api.get_playlist_detail(16199365))  # 我喜欢的列表
    # print(api.get_user_playlist())    # 我的列表
    print(api.search('linkin park'))
