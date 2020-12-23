"""
Model v2 design principles

1. as much compatable as possible
2. as less magic as possible
"""

from enum import IntFlag
from typing import List, Any, Optional

from pydantic import BaseModel

from feeluown.models import ModelType, ModelExistence
from feeluown.utils.utils import elfhash


class ModelFlags(IntFlag):
    none = 0x00000000

    v1 = 0x00000001
    v2 = 0x00000002

    brief = 0x00000010


class BaseModel(BaseModel):
    class meta:
        flags = ModelFlags.v2
        model_type = ModelType.dummy.value

    class Config:
        orm_mode = True

    identifier: str
    source: str = 'dummy'


class BaseBriefModel(BaseModel):
    """
    BaseBriefModel -> model display stage
    Model -> model gotten stage
    """
    class meta(BaseModel.meta):
        flags = BaseModel.meta.flags | ModelFlags.brief

    exists: ModelExistence = ModelExistence.unknown

    @classmethod
    def from_display_model(cls, model):
        data = {}
        for field in cls.__fields__:
            if field in ('identifier', 'source', 'exists'):
                value = getattr(model, field)
            else:
                value = getattr(model, f'{field}_display')
            data[field] = value
        return cls(**data)

    def __getattr__(self, attr):
        try:
            return super().__getattribute__(attr)
        except AttributeError:
            if attr.endswith('_display'):
                return getattr(self, attr[:-8])
            raise


class BriefSongModel(BaseBriefModel):
    class meta(BaseBriefModel.meta):
        model_type = ModelType.song

    title: str = ''
    artists_name: str = ''
    album_name: str = ''
    duration_ms: str = ''

    def __hash__(self):
        id_hash = elfhash(self.identifier.encode())
        return id_hash * 1000 + id(type(self)) % 1000


class BriefAlbumModel(BaseBriefModel):
    class meta(BaseBriefModel.meta):
        model_type = ModelType.album

    name: str = ''
    artists_name: str = ''


class BriefArtistModel(BaseBriefModel):
    class meta(BaseBriefModel.meta):
        model_type = ModelType.album

    name: str = ''


class SongModel(BaseModel):
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
