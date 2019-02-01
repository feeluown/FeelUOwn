import logging
import time
import os

from fuocore.models import (
    BaseModel,
    SongModel,
    LyricModel,
    PlaylistModel,
    AlbumModel,
    ArtistModel,
    SearchModel,
    UserModel,
)

from .provider import provider


logger = logging.getLogger(__name__)
MUSIC_LIBRARY_PATH = os.path.expanduser('~') + '/Music'


class NBaseModel(BaseModel):
    # FIXME: remove _detail_fields and _api to Meta
    _api = provider.api

    class Meta:
        allow_get = True
        provider = provider


class NSongModel(SongModel, NBaseModel):
    @classmethod
    def get(cls, identifier):
        data = cls._api.song_detail(int(identifier))
        song, _ = NeteaseSongSchema(strict=True).load(data)
        return song

    @classmethod
    def list(cls, identifiers):
        song_data_list = cls._api.songs_detail(identifiers)
        songs = []
        for song_data in song_data_list:
            song, _ = NeteaseSongSchema(strict=True).load(song_data)
            songs.append(song)
        return songs

    def _refresh_url(self):
        """刷新获取 url，失败的时候返回空而不是 None"""
        songs = self._api.weapi_songs_url([int(self.identifier)])
        if songs and songs[0]['url']:
            self.url = songs[0]['url']
        else:
            self.url = ''

    def _find_in_local(self):
        # TODO: make this a API in SongModel
        path = os.path.join(MUSIC_LIBRARY_PATH, self.filename)
        if os.path.exists(path):
            logger.debug('find local file for {}'.format(self))
            return path
        return None

    # NOTE: if we want to override model attribute, we must
    # implement both getter and setter.
    @property
    def url(self):
        """
        We will always check if this song file exists in local library,
        if true, we return the url of the local file.

        .. note::

            As netease song url will be expired after a period of time,
            we can not use static url here. Currently, we assume that the
            expiration time is 20 minutes, after the url expires, it
            will be automaticly refreshed.
        """
        local_path = self._find_in_local()
        if local_path:
            return local_path

        if not self._url:
            self._refresh_url()
        elif time.time() > self._expired_at:
            logger.info('song({}) url is expired, refresh...'.format(self))
            self._refresh_url()
        return self._url

    @url.setter
    def url(self, value):
        self._expired_at = time.time() + 60 * 20 * 1  # 20 minutes
        self._url = value

    @property
    def lyric(self):
        if self._lyric is not None:
            assert isinstance(self._lyric, LyricModel)
            return self._lyric
        data = self._api.get_lyric_by_songid(self.identifier)
        lrc = data.get('lrc', {})
        lyric = lrc.get('lyric', '')
        self._lyric = LyricModel(
            identifier=self.identifier,
            content=lyric
        )
        return self._lyric

    @lyric.setter
    def lyric(self, value):
        self._lyric = value


class NAlbumModel(AlbumModel, NBaseModel):

    @classmethod
    def get(cls, identifier):
        album_data = cls._api.album_infos(identifier)
        if album_data is None:
            return None
        album, _ = NeteaseAlbumSchema(strict=True).load(album_data)
        return album

    @property
    def desc(self):
        if self._desc is None:
            self._desc = self._api.album_desc(self.identifier)
        return self._desc

    @desc.setter
    def desc(self, value):
        self._desc = value


class NArtistModel(ArtistModel, NBaseModel):

    @classmethod
    def get(cls, identifier):
        artist_data = cls._api.artist_infos(identifier)
        artist = artist_data['artist']
        artist['songs'] = artist_data['hotSongs'] or []
        artist, _ = NeteaseArtistSchema(strict=True).load(artist)
        return artist

    @property
    def desc(self):
        if self._desc is None:
            self._desc = self._api.artist_desc(self.identifier)
        return self._desc

    @desc.setter
    def desc(self, value):
        self._desc = value


class NPlaylistModel(PlaylistModel, NBaseModel):
    class Meta:
        fields = ('uid')

    @classmethod
    def get(cls, identifier):
        data = cls._api.playlist_detail(identifier)
        playlist, _ = NeteasePlaylistSchema(strict=True).load(data)
        return playlist

    def add(self, song_id, allow_exist=True):
        rv = self._api.op_music_to_playlist(song_id, self.identifier, 'add')
        if rv == 1:
            song = NSongModel.get(song_id)
            self.songs.append(song)
            return True
        elif rv == -1:
            return True
        return False

    def remove(self, song_id, allow_not_exist=True):
        rv = self._api.op_music_to_playlist(song_id, self.identifier, 'del')
        if rv != 1:
            return False
        # XXX: make it O(1) if you want
        for song in self.songs:
            if song.identifier == song_id:
                self.songs.remove(song)
        return True


class NSearchModel(SearchModel, NBaseModel):
    pass


class NUserModel(UserModel, NBaseModel):
    class Meta:
        fields = ('cookies', )
        fields_no_get = ('cookies', )

    @classmethod
    def get(cls, identifier):
        user = {'id': identifier}
        user_brief = cls._api.user_brief(identifier)
        user.update(user_brief)
        playlists = cls._api.user_playlists(identifier)

        user['playlists'] = []
        user['fav_playlists'] = []
        for pl in playlists:
            if pl['userId'] == identifier:
                user['playlists'].append(pl)
            else:
                user['fav_playlists'].append(pl)
        user, _ = NeteaseUserSchema(strict=True).load(user)
        return user


def search(keyword, **kwargs):
    _songs = provider.api.search(keyword)
    id_song_map = {}
    songs = []
    if _songs:
        for song in _songs:
            id_song_map[str(song['id'])] = song
            schema = NeteaseSongSchema(strict=True)
            s, _ = schema.load(song)
            songs.append(s)
    return NSearchModel(q=keyword, songs=songs)


# import loop
from .schemas import (
    NeteaseSongSchema,
    NeteaseAlbumSchema,
    NeteaseArtistSchema,
    NeteasePlaylistSchema,
    NeteaseUserSchema,
)  # noqa
