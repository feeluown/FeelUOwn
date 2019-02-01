from fuocore.models import (
    BaseModel,
    SongModel,
    PlaylistModel,
    AlbumModel,
    ArtistModel,
    SearchModel,
    ModelStage,
)

from .provider import provider


class QQBaseModel(BaseModel):
    _api = provider.api

    class Meta:
        allow_get = True
        provider = provider
        fields = ('mid', )

    @classmethod
    def get(cls, identifier):
        raise NotImplementedError


def _deserialize(data, schema_cls):
    schema = schema_cls(strict=True)
    obj, _ = schema.load(data)
    # XXX: 将 model 设置为 gotten，减少代码编写时的心智负担，
    # 避免在调用 get 方法时进入无限递归。
    obj.stage = ModelStage.gotten
    return obj


class QQSongModel(SongModel, QQBaseModel):

    @classmethod
    def get(cls, identifier):
        data = cls._api.get_song_detail(identifier)
        song = _deserialize(data, QQSongDetailSchema)
        return song

    @property
    def url(self):
        if self._url is not None:
            return self._url
        url = self._api.get_song_url(self.mid)
        if url is not None:
            self._url = url
        else:
            self._url = ''
        return self._url

    @url.setter
    def url(self, url):
        self._url = url


class QQAlbumModel(AlbumModel, QQBaseModel):
    @classmethod
    def get(cls, identifier):
        data_album = cls._api.album_detail(identifier)
        album = _deserialize(data_album, QQAlbumSchema)
        album.cover = cls._api.get_cover(album.mid, 2)
        return album


class QQArtistModel(ArtistModel, QQBaseModel):
    @classmethod
    def get(cls, identifier):
        data_artist = cls._api.artist_detail(identifier)
        artist = _deserialize(data_artist, QQArtistSchema)
        artist.cover = cls._api.get_cover(artist.mid, 1)
        return artist


class QQPlaylistModel(PlaylistModel, QQBaseModel):
    pass


class QQSearchModel(SearchModel, QQBaseModel):
    pass


def search(keyword, **kwargs):
    data_songs = provider.api.search(keyword)
    songs = []
    for data_song in data_songs:
        song = _deserialize(data_song, QQSongSchema)
        songs.append(song)
    return QQSearchModel(songs=songs)


from .schemas import (
    QQArtistSchema,
    QQAlbumSchema,
    QQSongSchema,
    QQSongDetailSchema,
)  # noqa
