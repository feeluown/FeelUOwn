# -*- coding: utf8 -*-

import hashlib, time

from base.logger import LOG
from base.common import singleton
from base.models import MusicModel, UserModel, PlaylistModel, ArtistModel, \
    AlbumModel, BriefPlaylistModel, BriefMusicModel, BriefArtistModel, BriefAlbumModel
from plugin.NetEase.api import NetEase


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
    song = MusicModel(music_data).get_model()

    for i, artist in enumerate(song['artists']):
        artist_ = ArtistModel(artist).get_model()
        song['artists'][i] = artist_

    song['album'] = AlbumModel(song['album']).get_model()
    return song


def access_brief_music(music_data):

    song = BriefMusicModel(music_data).get_model()

    for i, artist in enumerate(song['artists']):
        artist = BriefArtistModel(artist).get_model()
        song['artists'][i] = artist

    song['album'] = BriefAlbumModel(song['album']).get_model()
    return song


def access_user(user_data):
    user_data['avatar'] = user_data['profile']['avatarUrl']
    user_data['uid'] = user_data['account']['id']
    user_data['username'] = user_data['profile']['nickname']
    user = UserModel(user_data).get_model()
    return user


def web_cache(func):
    data = {}

    def cache(this, *args, **kw):
        if args[0] in data:
            LOG.info('playlist: ' + data[args[0]]['name'] + ' has been cached')
        else:
            data[args[0]] = func(this, *args, **kw)
        return data[args[0]]
    return cache


@singleton
class NetEaseAPI(object):
    """
    根据标准的数据模型将 网易云音乐的数据 进行格式化

    这个类也需要管理一个数据库，这个数据库中缓存过去访问过的歌曲、列表、专辑图片等信息，以减少网络访问
    """
    def __init__(self):
        super().__init__()
        self.ne = NetEase()
        self.uid = 18731323

    def get_uid(self):
        return self.uid

    def check_res(self, data):
        flag = True
        if data['code'] == 408:
            data['message'] = u'貌似网络断了'
            flag = False
        else:
            data['message'] = u'联网成功'
            flag = True
        return data, flag

    def login(self, username, password, phone=False):
        password = password.encode('utf-8')
        password = hashlib.md5(password).hexdigest()
        data = self.ne.login(username, password, phone)
        data, flag = self.check_res(data)
        if flag is not True:
            return data

        if data['code'] is 200:    # 如果联网成功
            self.uid = data['account']['id']
            data = access_user(data)
            data['code'] = 200
        return data

    def auto_login(self, username, pw_encrypt, phone=False):
        """login into website with username and password which has been ecrypted
        """
        data = self.ne.login(username, pw_encrypt, phone)
        data, flag = self.check_res(data)
        if flag is not True:
            return data

        if data['code'] is 200:    # 如果联网成功
            self.uid = data['account']['id']
            data = access_user(data)
            data['code'] = 200
        return data

    def get_captcha_url(self, captcha_id):
        return self.ne.get_captcha_url(captcha_id)

    def confirm_captcha(self, captcha_id, text):
        data = self.ne.confirm_captcha(captcha_id, text)
        if data['result'] is False:
            return data['result'], data['captchaId']
        else:
            return data['result'], None

    def get_song_detail(self, mid):
        data = self.ne.song_detail(mid)
        songs = []
        for each in data:
            song = access_music(each)
            songs.append(song)
        return songs

    @web_cache
    def get_playlist_detail(self, pid):
        """貌似这个请求会比较慢

        :param pid:
        :return:
        """
        LOG.info(time.ctime())
        data = self.ne.playlist_detail(pid)     # 当列表内容多的时候，耗时严重
        LOG.info(time.ctime())

        data['uid'] = data['userId']
        data['type'] = data['specialType']

        for i, track in enumerate(data['tracks']):
            data['tracks'][i] = access_music(track)
        model = PlaylistModel(data).get_model()
        return model

    # @login_required     # 装饰器，挺好玩(装逼)的一个东西
    def get_user_playlist(self):
        data = self.ne.user_playlist(self.uid)

        for i, brief_playlist in enumerate(data):
            brief_playlist['uid'] = brief_playlist['userId']
            brief_playlist['type'] = brief_playlist['specialType']
            data[i] = BriefPlaylistModel(brief_playlist).get_model()
        return data

    def search(self, s, stype=1, offset=0, total='true', limit=60):
        data = self.ne.search(s, stype=1, offset=0, total='true', limit=60)
        songs = data['result']['songs']
        for i, song in enumerate(songs):
            songs[i] = access_brief_music(song)
        return songs

    def is_playlist_mine(self, playlist_model):
        if playlist_model['uid'] == self.uid:
            return True
        return False


if __name__ == "__main__":
    api = NetEaseAPI()
    # print(api.get_song_detail(17346999))    # Thank you
    # print(api.get_playlist_detail(16199365))  # 我喜欢的列表
    # print(api.get_user_playlist())    # 我的列表
    print(api.search('linkin park'))
