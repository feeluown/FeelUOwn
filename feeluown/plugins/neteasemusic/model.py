import json
import os

from feeluown.model import SongModel, PlaylistModel

from .api import api
from .consts import USERS_INFO_FILE


class NSongModel(SongModel):
    _api = api

    def __init__(self, mid, title, url, length, artists_model, album_model,
                 mvid=0):
        self.mid = mid
        self._title = title
        self._url = url
        self._length = length
        self.artists = artists_model
        self.album = album_model
        self.mvid = mid

    @property
    def title(self):
        return self._title

    @property
    def artists_name(self):
        name = []
        for artist in self.artists:
            name.append(artist.name)
        return ','.join(name)

    @property
    def album_name(self):
        return self.album.name

    @property
    def album_img(self):
        return self.album.img

    @property
    def length(self):
        return self._length

    @property
    def url(self):
        return self._url

    @classmethod
    def get(cls, mid):
        data = cls._api.song_detail(mid)
        return cls.create(data)

    @classmethod
    def create(cls, data):
        if data is None or not len(data['songs']):
            return None
        song_data = data['songs'][0]
        return cls.pure_create(song_data)

    @classmethod
    def pure_create(cls, song_data):
        mid = song_data['id']
        title = song_data['name']
        url = song_data['mp3Url']
        length = song_data['duration']
        album = _AlbumModel(song_data['album']['id'],
                            song_data['album']['name'],
                            song_data['album']['picUrl'])
        artists = [_ArtistModel(x['id'], x['name'])
                   for x in song_data['artists']]
        mvid = song_data['mvid']
        model = cls(mid, title, url, length, artists, album, mvid)
        return model

    @classmethod
    def batch_create(cls, datas):
        return [cls.pure_create(data) for data in datas]


class _AlbumModel(object):
    '''netease brief album model'''

    def __init__(self, bid, name, img):
        super().__init__()

        self.bid = bid
        self.name = name
        self.img = img


class _ArtistModel(object):
    def __init__(self, aid, name):
        super().__init__()
        self.aid = aid
        self.name = name


class NAlbumModel(object):
    _api = api

    def __init__(self, bid, name, artists_name, songs, img='', desc=''):
        super().__init__()

        self.bid = bid
        self._name = name
        self._artists_name = artists_name
        self._songs = songs
        self._img = img
        self._desc = desc

    @property
    def name(self):
        return self._name

    @property
    def artists_name(self):
        return self._artists_name

    @property
    def img(self):
        return self._img

    @property
    def songs(self):
        return self._songs

    @property
    def desc(self):
        return self._desc

    @classmethod
    def get(cls, bid):
        data = cls._api.album_infos(bid)
        return cls.create(data)

    @classmethod
    def create(cls, data):
        if data is None or data['code'] != 200:
            return None
        album_data = data['album']
        bid = album_data['id']
        name = album_data['name']
        artists_name = album_data['artist']['name']
        songs = NSongModel.batch_create(album_data['songs'])
        img = album_data['picUrl']
        desc = album_data['briefDesc']
        return NAlbumModel(bid, name, artists_name, songs, img, desc)


class NArtistModel(object):
    _api = api

    def __init__(self, aid, name, img, songs=[]):
        self.aid = aid
        self._name = name

        self.img = img
        self.songs = songs

    @property
    def name(self):
        return self._name

    @classmethod
    def get(cls, aid):
        data = cls._api.artist_infos(aid)
        return cls.create(data)

    @classmethod
    def create(cls, data):
        if data is None or data['code'] != 200:
            return None

        aid = data['artist']['id']
        name = data['artist']['name']
        img = data['artist']['picUrl']

        songs = NSongModel.batch_create(data['hotSongs'])
        return cls(aid, name, img, songs)


class NUserModel(object):
    _api = api

    def __init__(self, username, uid, name, img, playlists=[]):
        super().__init__()
        self.username = username

        self.uid = uid
        self.name = name
        self.img = img
        self._playlists = playlists

    @property
    def playlists(self):
        if self._playlists:
            return self._playlists
        data = self._api.user_playlist(self.uid)
        if data is None:
            return []
        playlists = data['playlist']
        playlists_model = []
        for p in playlists:
            model = NPlaylistModel(p['id'], p['name'], p['specialType'],
                                   p['uid'])
            playlists_model.append(model)
        self._playlists = playlists_model
        return playlists_model

    @classmethod
    def create(cls, data):
        user_data = data['data']
        username = data['username']
        img = user_data['profile']['avatarUrl']
        uid = user_data['profile']['userId']
        name = user_data['profile']['nickname']
        model = NUserModel(username, uid, name, img)
        return model

    @classmethod
    def check(cls, username, pw):
        data = cls._api.login(username, pw)
        if data is None:
            return {'code': 408, 'message': '网络状况不好'}
        elif data['code'] == 200:
            return {'code': 200, 'message': '登陆成功',
                    'data': data, 'username': username}
        elif data['code'] == 415:
            captcha_id = data['captchaId']
            url = cls._api.get_captcha_url(captcha_id)
            return {'code': 415, 'message': '本次登陆需要验证码',
                    'captcha_url': url, 'captchar_id': captcha_id}
        elif data['code'] == 501:
            return {'code': 501, 'message': '用户名不存在'}
        elif data['code'] == 502:
            return {'code': 502, 'message': '密码错误'}
        elif data['code'] == 509:
            return {'code': 509, 'message': '请休息几分钟再尝试'}

    @classmethod
    def check_captcha(cls, captcha_id, text):
        flag, cid = cls._api.confirm_captcha(captcha_id, text)
        if flag is not True:
            url = cls._api.get_captcha_url(cid)
            return {'code': 415, 'message': '验证码错误',
                    'captcha_url': url, 'captcha_id': cid}
        return {'code': 200, 'message': '验证码正确'}

    def save(self):
        with open(USERS_INFO_FILE, 'w+') as f:
            data = {
                self.username: {
                    'uid': self.uid,
                    'name': self.name,
                    'img': self.img,
                    'cookies': self._api.cookies
                }
            }
            if f.read() != '':
                data.update(json.load(f))
            json.dump(data, f, indent=4)

    @classmethod
    def load(cls):
        if not os.path.exists(USERS_INFO_FILE):
            return None
        with open(USERS_INFO_FILE, 'r') as f:
            text = f.read()
            if text == '':
                return None
            data = json.loads(text)
            username = next(iter(data.keys()))
            user_data = data[username]
            model = cls(username,
                        user_data['uid'],
                        user_data['name'],
                        user_data['img'])
            model._api.load_cookies(user_data['cookies'])
        return model


class NPlaylistModel(PlaylistModel):
    _api = api

    def __init__(self, pid, name, ptype, uid, songs=[]):
        super().__init__()
        self.pid = pid
        self._name = name
        self.ptype = ptype
        self.uid = uid
        self._songs = songs

    @property
    def name(self):
        return self._name

    @property
    def songs(self):
        if self._songs:
            return self._songs
        data = self._api.playlist_detail(self.pid)
        if data is None:
            return None
        songs_model = NSongModel.batch_create(data['result']['tracks'])
        self._songs = songs_model
        return self._songs
