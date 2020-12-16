# -*- coding: utf-8 -*-

from feeluown.utils.reader import SequentialReader as GeneratorProxy  # noqa, for backward compatible
from .base import (
    cached_field, ModelType, Model, ModelExistence, ModelStage,
    SearchType, AlbumType, display_property,
)
from .models import (
    BaseModel, LyricModel,
    SongModel, AlbumModel, ArtistModel, PlaylistModel,
    UserModel, MvModel, SearchModel, VideoModel,
)
from .uri import (
    resolve,
    reverse,
    Resolver,
    ResolveFailed,
    ResolverNotFound,
)  # noqa

__all__ = (
    'resolve',
    'reverse',
    'ResolveFailed',
    'ResolverNotFound',  # TODO: should not expose Resolver conceptt
    'Resolver',
    'cached_field',

    # base
    'display_property',
    'cached_field',
    'ModelType',
    'Model',
    'ModelExistence',
    'ModelStage',

    'AlbumType',
    'SearchType',

    # models
    'BaseModel',
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
