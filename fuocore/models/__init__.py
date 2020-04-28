# -*- coding: utf-8 -*-

from fuocore.reader import SequentialReader as GeneratorProxy  # noqa, for backward compatible
from .base import cached_field, BaseModel, ModelType, Model, \
    display_property, ModelExistence, ModelStage
from .song import SongModel
from .artist import ArtistModel
from .album import AlbumModel, AlbumType
from .search import SearchModel, SearchType
from .playlist import PlaylistModel
from .user import UserModel
from .mv import MvModel
from .lyric import LyricModel
from .video import VideoModel
from .uri import (
    resolve,
    reverse,
    Resolver,
    ResolveFailed,
    ResolverNotFound,
)


__all__ = (
    'resolve',
    'reverse',
    'ResolveFailed',
    'ResolverNotFound',  # TODO: should not expose Resolver concept
    'Resolver',

    # base
    'display_property',
    'cached_field',
    'BaseModel',
    'ModelType',
    'Model',
    'ModelExistence',
    'ModelStage',

    'AlbumType',
    'SearchType',

    # models
    'SongModel',
    'AlbumModel',
    'ArtistModel',
    'PlaylistModel',
    'UserModel',
    'SearchModel',
    'LyricModel',
    'MvModel',
    'VideoModel',
)
