import datetime
import json
import logging
import os

from feeluown.model import SongModel, PlaylistModel
from feeluown.consts import SONG_DIR

from .api import api
from .consts import USERS_INFO_FILE, SOURCE

logger = logging.getLogger(__name__)


class NSongModel(SongModel):
    _api = api

    def __init__(self, mid, title, length, artists_model, album_model,
                 mvid=0, url=None):
        self._mid = mid
        self._title = title
        self._url = None
        self._candidate_url = url
        self._length = length
        self.artists = artists_model
        self.album = album_model
        self.mvid = mid

        self._start_time = datetime.datetime.now()

    @property
    def mid(self):
        return self._mid

    @property
    def title(self):
        return self._title

    @property
    def artists_name(self):
        name = []
        for artist in self.artists:
            name.append(artist.name)
        return ', '.join(name)

    @property
    def album_name(self):
        return self.album.name

    @property
    def album_img(self):
        if not self.album._img:
            logger.debug('songs has no album img, so get detail')
            self.get_detail()
        return self.album.img

    @property
    def length(self):
        return self._length

    @property
    def source(self):
        return SOURCE

    @property
    def url(self):
        f_path = NSongModel.local_exists(self)
        if f_path is not None:
            logger.info('use local mp3 file for song: %s' % self.title)
            return f_path

        if self._url is not None:   # use cached url
            now = datetime.datetime.now()
            if (now - self._start_time).total_seconds() / 60 > 10:
                logger.warning('%s url maybe outdated.' % (self.title))
                self._url = None
                return self.url
            return self._url

        data = self._api.weapi_songs_url([self.mid])
        if data is not None:
            if data['code'] == 200:
                # get when needed as url will be invalid several minute later
                url = data['data'][0]['url']
                if url is None:
                    return self.candidate_url

                self._start_time = datetime.datetime.now()
                self._url = url
                return url
            if data['code'] == 404:
                return self.candidate_url
        return self._url

    @property
    def candidate_url(self):
        self._candidate_url = self._api.get_xiami_song_by_title(self.title)
        if self._candidate_url:
            logger.info('use xiami url for song: %s, the url is: %s'
                        % (self.title, self._candidate_url))
        else:
            self.get_detail()
        return self._candidate_url

    def get_detail(self):
        data = self._api.song_detail(self.mid)
        if data is not None:
            song = data['songs'][0]
            self._candidate_url = song['mp3Url']
            self.album._img = song['album']['picUrl']

    def get_simi_songs(self):
        data = self._api.get_similar_song(self.mid)
        if data is None:
            return []
        if data['code'] == 200:
            return [NSongModel.pure_create(data['songs'][0])]
        else:
            return []

    @classmethod
    def mv_available(cls, mvid):
        if mvid != 0:
            return True
        return False

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
        url = song_data.get('mp3Url', None)
        length = song_data['duration']
        album = NAlbumModel.create_from_brief(song_data['album'])
        artists = [NArtistModel(x['id'], x['name'])
                   for x in song_data['artists']]
        mvid = song_data['mvid']
        model = cls(mid, title, length, artists, album, mvid, url)
        return model

    @classmethod
    def batch_create(cls, datas):
        return [cls.pure_create(data) for data in datas]

    @classmethod
    def search(cls, text):
        data = cls._api.search(text)
        songs = []
        if data is not None and 'result' in data.keys():
            if data['result']['songCount']:
                songs = data['result']['songs']
        return cls.batch_create(songs)

    # TODO: some songs may have same title and artists_name, temp ignore
    @property
    def filename(self):
        return self._title + ' - ' + self.artists_name + '.mp3'

    @classmethod
    def local_exists(cls, song):
        '''return song file path if exists, else None'''
        f_name = song.filename
        f_path = os.path.join(SONG_DIR, f_name)
        if os.path.exists(f_path):
            return f_path
        else:
            return None


class NAlbumModel(object):
    _api = api

    def __init__(self, bid, name, artists_name, songs=[], img='', desc=''):
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
        if not self._img:
            logger.debug('album has no img, so get detail')
            self.get_detail()
        return self._img

    @property
    def img_id(self):
        return SOURCE + '-' + 'album' + str(self.bid)

    @property
    def songs(self):
        if not self._songs:
            logger.debug('album has no songs, so get detail')
            self.get_detail()
        return self._songs

    @property
    def desc(self):
        if not self._desc:
            self._desc = self._api.album_desc(self.bid)
        return self._desc

    @classmethod
    def create_from_brief(cls, data):
        pid = data['id']
        name = data['name']
        if 'artists' in data:
            artists_name = ', '.join([x['name'] for x in data['artists']])
        else:
            artists_name = data['artist']
        img = data.get('picUrl', None)
        return cls(pid, name, artists_name, img=img)

    def get_detail(self):
        data = self._api.album_infos(self.bid)
        if data is not None:
            data = data['album']
            self._songs = NSongModel.batch_create(data['songs'])
            self._img = data['picUrl']
            self._desc = data['description']

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

    def __init__(self, aid, name, img='', songs=[]):
        self.aid = aid
        self._name = name

        self._img = img
        self._desc = ''
        self._songs = songs

    @property
    def name(self):
        return self._name

    @property
    def img(self):
        if not self._img:
            logger.debug('artist has no img, so get detail')
            self.get_detail()
        return self._img

    @property
    def img_id(self):
        return SOURCE + '-' + 'artist' + str(self.aid)

    @property
    def desc(self):
        if not self._desc:
            self._desc = self._api.artist_desc(self.aid)
        return self._desc

    @property
    def songs(self):
        if not self._songs:
            logger.debug('artist has no songs, so get detail')
            self.get_detail()
        return self._songs

    def get_detail(self):
        data = self._api.artist_infos(self.aid)
        if data is not None:
            self._img = data['artist']['picUrl']
            self._description = data['description']
            self._songs = NSongModel.batch_create(data['hotSongs'])

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
    current_user = None

    def __init__(self, username, uid, name, img, playlists=[]):
        super().__init__()
        self.username = username

        self.uid = uid
        self.name = name
        self.img = img
        self._playlists = playlists

    def is_playlist_mine(self, pid):
        for p in self.playlists:
            if p.pid == pid:
                return True
        return False

    @classmethod
    def set_current_user(cls, user):
        cls.current_user = user

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
                                   p['userId'], p['coverImgUrl'],
                                   p['updateTime'], p['description'])
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

    @classmethod
    def get_recommend_songs(cls):
        if cls.current_user is None:
            return []
        data = cls._api.get_recommend_songs()
        if data.get('code') == 200:
            return NSongModel.batch_create(data['recommend'])
        return []

    @classmethod
    def get_fm_song(cls):
        if cls.current_user is None:
            return []
        data = cls._api.get_radio_music()
        if data is None:
            return []
        if data['code'] == 200:
            songs = data['data']
            return NSongModel.batch_create(songs)
        else:
            return []


class NPlaylistModel(PlaylistModel):
    instances = []
    _api = api

    def __init__(self, pid, name, ptype, uid, cover_img, update_ts,
                 description, songs=[]):
        super().__init__()
        self.pid = pid
        self._name = name
        self.ptype = ptype
        self.uid = uid
        self._songs = songs
        self.cover_img = cover_img
        self._description = description
        self.last_update_ts = update_ts

        NPlaylistModel.instances.append(self)

    @property
    def name(self):
        return self._name

    @property
    def cover_img_id(self):
        return SOURCE + '-' + 'playlist' + '-' + str(self.last_update_ts)

    @property
    def desc(self):
        return self._description

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

    def update_songs(self):
        self._songs = []

    def add_song(self, mid):
        data = self._api.op_music_to_playlist(mid, self.pid, op='add')
        if data is None:
            return False
        if data['code'] == 502:
            return False
        elif data['code'] == 200:
            self.update_songs()
            return True

    def del_song(self, mid):
        data = self._api.op_music_to_playlist(mid, self.pid, op='del')
        if data.get('code') == 200:
            self.update_songs()
            return True
        return False

    @classmethod
    def del_song_from_playlist(cls, mid, pid):
        for playlist in cls.instances:
            if playlist.pid == pid:
                return playlist.del_song(mid)
        data = cls._api.op_music_to_playlist(mid, pid, op='del')
        if data['code'] == 200:
            return True
        return False

    @classmethod
    def is_favorite(cls, model):
        if model.ptype == 5:
            return True
