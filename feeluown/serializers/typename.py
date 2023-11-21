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
r_typenames = dict(r_typenames)


def get_type_by_name(name: str):
    return typenames.get(name, None)


def get_names_by_type(type_: Any):
    # try except so that performance is not affected.
    try:
        return r_typenames[type_]
    except KeyError:
        if type_.__module__ == 'unittest.mock':
            return ['unittest.mock.Mock']
        return []


def attach_typename(method):

    def wrapper(this, obj, **kwargs):
        result = method(this, obj, **kwargs)
        if isinstance(result, dict):
            typenames = get_names_by_type(type(obj))
            if typenames:
                result['__type__'] = typenames[0]
            else:
                result['__type__'] = 'to_be_added__pr_is_welcome'
        return result

    return wrapper
