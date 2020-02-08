# -*- coding: utf-8 -*-

"""
fuocore.provider
~~~~~~~~~~~~~~~~

"""
from abc import ABC, abstractmethod
from contextlib import contextmanager
from fuocore.models import (
    SongModel,
    ArtistModel,
    AlbumModel,
    PlaylistModel,
    LyricModel,

    UserModel,

    ModelType,
)


_TYPE_NAME_MAP = {
    ModelType.song: 'Song',
    ModelType.artist: 'Artist',
    ModelType.album: 'Album',
    ModelType.playlist: 'Playlist',
    ModelType.lyric: 'Lyric',
    ModelType.user: 'User',
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


class DummyProvider(AbstractProvider):

    @property
    def identifier(self):
        return 'dummy'

    @property
    def name(self):
        return 'dummy'


dummy_provider = DummyProvider()
