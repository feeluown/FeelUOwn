# -*- coding: utf-8 -*-

"""
feeluown.library
~~~~~~~~~~~~~~~~

"""
from abc import ABC, abstractmethod
from contextlib import contextmanager
from feeluown.models import (
    BaseModel,
    SongModel,
    ArtistModel,
    AlbumModel,
    PlaylistModel,
    LyricModel,
    VideoModel,

    UserModel,

    SearchModel,

    ModelType,
)


_TYPE_NAME_MAP = {
    ModelType.song: 'Song',
    ModelType.artist: 'Artist',
    ModelType.album: 'Album',
    ModelType.playlist: 'Playlist',
    ModelType.lyric: 'Lyric',
    ModelType.user: 'User',
    ModelType.video: 'Video',
}


class AbstractProvider(ABC):
    """abstract music resource provider
    """

    # A well behaved provider should implement its own models .
    Song = SongModel
    Artist = ArtistModel
    Album = AlbumModel
    Playlist = PlaylistModel
    Lyric = LyricModel
    User = UserModel
    Video = VideoModel

    def __init__(self):
        self._user = None

    def get_model_cls(self, model_type):
        name = _TYPE_NAME_MAP[model_type]
        return getattr(self, name)

    def set_model_cls(self, model_type, model_cls):
        name = _TYPE_NAME_MAP[model_type]
        setattr(self, name, model_cls)

    @property
    @abstractmethod
    def identifier(self):
        """provider identify"""

    @property
    @abstractmethod
    def name(self):
        """provider name"""

    @contextmanager
    def auth_as(self, user):
        """auth as a user temporarily

        Usage::

            with auth_as(user):
                ...
        """
        old_user = self._user
        self.auth(user)
        try:
            yield
        finally:
            self.auth(old_user)

    def auth(self, user):
        """use provider as a specific user"""
        self._user = user

    def search(self, *args, **kwargs):
        pass


Dummy = 'dummy'


class DummyProvider(AbstractProvider):
    """dummy provider, mainly for debug/testing

    People often need a mock/dummy/fake provider/song/album/artist
    for debug/testing, so we designed this dummy provider.

    .. note::

        We MAY add new fields for those models, and we SHOULD not change
        the value of existings fields as much as possible.
    """

    @property
    def identifier(self):
        return Dummy

    @property
    def name(self):
        return 'Dummy'

    def search(self, *args):
        return DummySearchModel(
            q=Dummy,
            songs=[DummySongModel.get(Dummy)],
            artists=[DummyArtistModel.get(Dummy)],
            albums=[DummyAlbumModel.get(Dummy)],
            playlists=[DummyPlaylistModel.get(Dummy)],
        )


dummy_provider = DummyProvider()


class DummyBaseModel(BaseModel):
    class Meta:
        allow_get = True
        provider = dummy_provider


class DummySongModel(SongModel, DummyBaseModel):
    """
    >>> song = dummy_provider.Song.get(Dummy)
    >>> song.title
    'dummy'
    """

    @classmethod
    def get(cls, identifier):
        if identifier == Dummy:
            return cls(
                identifier=Dummy,
                title=Dummy,
                duration=0,
                artists=[DummyArtistModel.get(Dummy)],
                album=DummyAlbumModel.get(Dummy),
                url=Dummy,
            )
        return None


class DummyVideoModel(VideoModel, DummyBaseModel):
    @classmethod
    def get(cls, identifier):
        if identifier == Dummy:
            return cls(
                identifier=Dummy,
                title=Dummy,
                media=Dummy,
            )
        return None


class DummyArtistModel(ArtistModel, DummyBaseModel):
    @classmethod
    def get(cls, identifier):
        if identifier == Dummy:
            return cls(
                identifier=Dummy,
                name=Dummy,
            )


class DummyAlbumModel(AlbumModel, DummyBaseModel):
    @classmethod
    def get(cls, identifier):
        if identifier == Dummy:
            return cls(
                identifier=Dummy,
                name=Dummy,
            )


class DummyPlaylistModel(PlaylistModel, DummyBaseModel):
    @classmethod
    def get(cls, identifier):
        if identifier == Dummy:
            return cls(
                identifier=Dummy,
                name=Dummy,
            )


class DummyLyricModel(LyricModel, DummyBaseModel):
    @classmethod
    def get(cls, identifier):
        if identifier == Dummy:
            return cls(
                identifier=Dummy,
                song=DummySongModel.get(Dummy),
                content='',
            )


class DummyUserModel(UserModel, DummyBaseModel):
    @classmethod
    def get(cls, identifier):
        if identifier == Dummy:
            return cls(
                identifier=Dummy,
                name=Dummy,
            )


class DummySearchModel(SearchModel, DummyBaseModel):
    pass
