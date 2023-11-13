from collections import defaultdict
from typing import Any
from unittest.mock import Mock

from feeluown.app import App
from feeluown.player import Metadata
from feeluown.library import (
    BaseModel,
    SongModel,
    ArtistModel,
    AlbumModel,
    PlaylistModel,
    UserModel,
    BriefSongModel,
    BriefArtistModel,
    BriefAlbumModel,
    BriefPlaylistModel,
    BriefUserModel,
)

model_cls_list = [
    BaseModel,
    SongModel,
    ArtistModel,
    AlbumModel,
    PlaylistModel,
    UserModel,
    BriefSongModel,
    BriefArtistModel,
    BriefAlbumModel,
    BriefPlaylistModel,
    BriefUserModel,
]

_sys_typenames = {  # for unittest.
    'unittest.mock.Mock': Mock
}
_typenames = {
    'player.Metadata': Metadata,
    'app.App': App,  # TODO: remove this
}
for model_cls in model_cls_list:
    _typenames[f'library.{model_cls.__name__}'] = model_cls
typenames = {f'feeluown.{k}': v for k, v in _typenames.items()}
typenames.update(_sys_typenames)

r_typenames = defaultdict(list)
for k, v in typenames.items():
    r_typenames[v].append(k)


def get_type_by_name(name: str):
    return typenames.get(name, None)


def get_names_by_type(type_: Any):
    return r_typenames.get(type_, [])


def attach_typename(method):

    def wrapper(this, obj, **kwargs):
        result = method(this, obj, **kwargs)
        if isinstance(result, dict):
            typenames = get_names_by_type(type(obj))
            assert typenames, f'no typename for {type(obj)}'
            result['__type__'] = typenames[0]
        return result

    return wrapper
