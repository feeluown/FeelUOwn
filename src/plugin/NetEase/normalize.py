# -*- coding: utf8 -*-

import hashlib

from base.common import singleton
from base.models import MusicModel, UserModel, PlaylistModel, ArtistModel, \
    AlbumModel, BriefPlaylistModel, BriefMusicModel, BriefArtistModel, BriefAlbumModel
from plugin.NetEase.api import NetEase


def login_required(func):
    def wrapper(*args):
        this = args[0]
        if this.uid == 0:
            return {'code': 401}    # Unauthorized
        func(*args)
    return wrapper


def access_music(music_data):
    music_data['url'] = music_data['mp3Url']
    song = MusicModel(music_data).get_model()

    for i, artist in enumerate(song['artists']):
        artist = ArtistModel(artist).get_model()
        song['artists'][i] = artist

    song['album'] = AlbumModel(song['album']).get_model()
    return song

def access_brief_music(music_data):

    song = BriefMusicModel(music_data).get_model()

    for i, artist in enumerate(song['artists']):
        artist = BriefArtistModel(artist).get_model()
        song['artists'][i] = artist

    song['album'] = BriefAlbumModel(song['album']).get_model()
    return song

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
            data['message'] = u'操作成功'
            flag = True
        return data, flag

    def login(self, username, password, phone=False):
        password = password.encode('utf-8')
        password = hashlib.md5(password).hexdigest()
        data = self.ne.login(username, password, phone)
        data, flag = self.check_res(data)
        if flag is True:
            self.uid = data['account']['id']
        return UserModel(data).get_model()

    def auto_login(self, username, pw_encrypt, phone=False):
        """login into website with username and password which has been ecrypted
        """
        data = self.ne.login(username, pw_encrypt, phone)
        data, flag = self.check_res(data)
        if flag is True:
            self.uid = data['account']['id']
        return data

    def get_song_detail(self, mid):
        data = self.ne.song_detail(mid)
        songs = []
        for each in data:
            song = access_music(each)
            songs.append(song)
        return songs

    def get_playlist_detail(self, pid):
        """貌似这个请求会比较慢

        :param pid:
        :return:
        """
        data = self.ne.playlist_detail(pid)

        for i, track in enumerate(data['tracks']):
            data['tracks'][i] = access_music(track)
        return PlaylistModel(data).get_model()

    # @login_required     # 装饰器，挺好玩(装逼)的一个东西
    def get_user_playlist(self):
        data = self.ne.user_playlist(self.uid)
        for i, brief_playlist in enumerate(data):
            data[i] = BriefPlaylistModel(brief_playlist).get_model()
        return data

    def search(self, s, stype=1, offset=0, total='true', limit=60):
        data = self.ne.search(s, stype=1, offset=0, total='true', limit=60)
        songs = data['result']['songs']
        for i, song in enumerate(songs):
            songs[i] = access_brief_music(song)
        return songs


if __name__ == "__main__":
    api = NetEaseAPI()
    # print(api.get_song_detail(17346999))    # Thank you
    # print(api.get_playlist_detail(16199365))  # 我喜欢的列表
    # print(api.get_user_playlist())    # 我的列表
    print(api.search('linkin park'))
