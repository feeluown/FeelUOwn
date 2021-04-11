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


def cook_artists_name(names):
    # [a, b, c] -> 'a, b & c'
    artists_name = ', '.join(names)
    return ' & '.join(artists_name.rsplit(', ', 1))


class ModelFlags(IntFlag):
    none = 0x00000000

    v1 = 0x00000001
    v2 = 0x00000002

    brief = 0x00000010
    normal = brief | 0x00000020


class ModelMeta:
    def __init__(self, flags, model_type):
        self.flags = flags
        self.model_type = model_type

    @classmethod
    def create(cls, model_type=ModelType.dummy, is_brief=False, is_normal=False):
        flags = ModelFlags.v2
        assert not (is_brief is is_normal is True)
        if is_brief is True:
            flags |= ModelFlags.brief
        if is_normal is True:
            flags |= ModelFlags.normal
        return cls(model_type=model_type, flags=flags)


class BaseModel(_BaseModel):
    class Config:
        # Do not use Model.from_orm to convert v1 model to v2 model
        # since v1 model has too much magic.
        orm_mode = False
        # Forbidding extra fields is good for debugging. The default behavior
        # is a little implicit. If you want to store an extra attribute on model,
        # use :meth:`cache_set` explicitly.
        extra = 'forbid'

    __cache__: dict = PrivateAttr(default_factory=dict)
    meta: Any = ModelMeta.create()

    identifier: str
    # Before, the default value of source is 'dummy', which is too implicit.
    source: str = 'dummy'
    state: ModelState = ModelState.artificial

    #: (DEPRECATED) for backward compact
    exists: ModelExistence = ModelExistence.unknown

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
    meta: Any = ModelMeta.create(is_brief=True)

    @classmethod
    def from_display_model(cls, model):
        """Create a new model from an old model in display stage.

        This method never triggers IO operations.
        """
        # Due to the display_property mechanism, it is unsafe to
        # get attribute of other stage model property.
        assert model.stage is ModelStage.display
        data = {'state': cls._guess_state_from_exists(model.exists)}
        for field in cls.__fields__:
            if field in ('state', 'meta'):
                continue
            if field in ('identifier', 'source', 'exists'):
                value = object.__getattribute__(model, field)
            else:
                assert field in model.meta.fields_display, \
                    f'{field} must be a display field'
                value = getattr(model, f'{field}_display')
            data[field] = value
        return cls(**data)

    @classmethod
    def _guess_state_from_exists(cls, exists):
        if exists == ModelExistence.no:
            state_value = ModelState.not_exists
        elif exists == ModelExistence.unknown:
            state_value = ModelState.artificial
        else:
            state_value = ModelState.exists
        return state_value


class BaseNormalModel(BaseModel):
    meta: Any = ModelMeta.create(is_normal=False)
    state: ModelState = ModelState.upgraded


class BriefSongModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.song, is_brief=True)
    title: str = ''
    artists_name: str = ''
    album_name: str = ''
    duration_ms: str = ''


class BriefAlbumModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.album, is_brief=True)
    name: str = ''
    artists_name: str = ''


class BriefArtistModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.artist, is_brief=True)
    name: str = ''


class SongModel(BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.song, is_normal=True)
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
    meta: Any = ModelMeta.create(ModelType.user, is_brief=True)
    name: str = ''


class UserModel(BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.user, is_normal=True)
    name: str = ''
    avatar_url: str = ''


class BriefCommentModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.comment, is_brief=True)
    user_name: str = ''
    content: str = ''


class CommentModel(BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.comment, is_normal=True)
    user: BriefUserModel
    content: str
    #: -1 means that the provider does not have such data
    liked_count: int
    #: unix timestamp, for example 1591695620
    time: int
    #: the parent comment which this comment replies to
    parent: Optional[BriefCommentModel]
    #: the root comment id
    root_comment_id: Optional[str]
