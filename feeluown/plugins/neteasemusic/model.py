from feeluown.model import SongModel


class NSongModel(SongModel):
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
    def __init__(self, aid, name, img, songs=[]):
        self.aid = aid
        self._name = name

        self.img = img
        self.songs = songs

    @property
    def name(self):
        return self._name

    @classmethod
    def create(cls, data):
        if data is None or data['code'] != 200:
            return None

        aid = data['artist']['id']
        name = data['artist']['name']
        img = data['artist']['picUrl']

        songs = NSongModel.batch_create(data['hotSongs'])
        return cls(aid, name, img, songs)
