"""
Model v2 design principles

1. as much compatable as possible
2. as less magic as possible
"""

import time
from enum import IntFlag
from typing import List, Optional, Tuple, Any

from pydantic import BaseModel as _BaseModel, PrivateAttr

from feeluown.models import ModelType, ModelExistence, ModelStage
from feeluown.utils.utils import elfhash
from .model_state import ModelState


class ModelFlags(IntFlag):
    none = 0x00000000

    v1 = 0x00000001
    v2 = 0x00000002

    brief = 0x00000010
    normal = brief | 0x00000020


class BaseModel(_BaseModel):
    class meta:
        flags = ModelFlags.v2
        model_type = ModelType.dummy.value

    class Config:
        # Do not use Model.from_orm to convert v1 model to v2 model
        # since v1 model has too much magic.
        orm_mode = False
        # Forbidding extra fields is good for debugging. The default behavior
        # is a little implicit. If you want to store an extra attribute on model,
        # use :meth:`cache_set` explicitly.
        extra = 'forbid'

    __cache__: dict = PrivateAttr(default_factory=dict)

    identifier: str
    # Before, the default value of source is 'dummy', which is too implicit.
    source: str

    def cache_get(self, key) -> Tuple[Any, bool]:
        if key in self.__cache__:
            value, expired_at = self.__cache__[key]
            if expired_at is None or expired_at >= int(time.time()):
                return value, True
        return None, False

    def cache_set(self, key, value, ttl=None):
        """
        :param int ttl: the unit is seconds.
        """
        if ttl is None:
            expired_at = None
        else:
            expired_at = int(time.time()) + ttl
        self.__cache__[key] = (value, expired_at)

    def __hash__(self):
        id_hash = elfhash(self.identifier.encode())
        return id_hash * 1000 + id(type(self)) % 1000

    def __getattr__(self, attr):
        try:
            return super().__getattribute__(attr)
        except AttributeError:
            if attr.endswith('_display'):
                return getattr(self, attr[:-8])
            raise


class BaseBriefModel(BaseModel):
    """
    BaseBriefModel -> model display stage
    Model -> model gotten stage
    """
    class meta(BaseModel.meta):
        flags = BaseModel.meta.flags | ModelFlags.brief

    state: ModelState = ModelState.artificial
    # (DEPRECATED) for backward compact
    exists: ModelExistence = ModelExistence.unknown

    @classmethod
    def from_display_model(cls, model):
        assert model.stage is ModelStage.display
        data = {}
        for field in cls.__fields__:
            if field in ('state', ):
                continue
            if field in ('identifier', 'source', 'exists'):
                value = object.__getattribute__(model, field)
                if field == 'exists':
                    if value == ModelExistence.no:
                        state_value = ModelState.not_exists
                    elif value == ModelExistence.unknown:
                        state_value = ModelState.artificial
                    else:
                        state_value = ModelState.exists
                    data['state'] = state_value
            else:
                assert field in model.meta.fields_display
                value = getattr(model, f'{field}_display')
            data[field] = value
        return cls(**data)


class BaseNormalModel(BaseModel):
    class meta(BaseModel.meta):
        flags = BaseModel.meta.flags | ModelFlags.normal

    state: ModelState = ModelState.upgraded


class BriefSongModel(BaseBriefModel):
    class meta(BaseBriefModel.meta):
        model_type = ModelType.song

    title: str = ''
    artists_name: str = ''
    album_name: str = ''
    duration_ms: str = ''


class BriefAlbumModel(BaseBriefModel):
    class meta(BaseBriefModel.meta):
        model_type = ModelType.album

    name: str = ''
    artists_name: str = ''


class BriefArtistModel(BaseBriefModel):
    class meta(BaseBriefModel.meta):
        model_type = ModelType.artist

    name: str = ''


class SongModel(BaseNormalModel):
    class meta(BaseNormalModel.meta):
        model_type = ModelType.song

    title: str
    album: Optional[BriefAlbumModel]
    artists: List[BriefArtistModel]
    duration: int  # milliseconds

    @property
    def artists_name(self):
        # [a, b, c] -> 'a, b & c'
        artists_name = ', '.join((artist.name
                                  for artist in self.artists))
        return ' & '.join(artists_name.rsplit(', ', 1))

    @property
    def album_name(self):
        return self.album.name

    @property
    def duration_ms(self):
        if self.duration is not None:
            seconds = self.duration / 1000
            m, s = seconds / 60, seconds % 60
        else:
            m, s = 0, 0
        return '{:02}:{:02}'.format(int(m), int(s))


class BriefUserModel(BaseBriefModel):
    class Meta(BaseBriefModel.meta):
        model_type = ModelType.user

    name: str = ''
    avatar_url: str = ''


class CommentModel(BaseNormalModel):
    class Meta(BaseNormalModel.meta):
        model_type = ModelType.comment

    content: str
    parent_comment_id: str
    time: int  # unix timestamp, for example 1591695620
    user: BriefUserModel
