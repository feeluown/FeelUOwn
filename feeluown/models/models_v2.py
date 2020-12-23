"""
Model v2 design principles

1. as much compatable as possible
2. as less magic as possible
"""

from enum import IntFlag
from typing import List, Any, Optional

from pydantic import BaseModel

from .base import ModelType, ModelExistence


class ModelFlags(IntFlag):
    none = 0x00000000

    v1 = 0x00000001
    v2 = 0x00000002

    brief = 0x00000010


class BaseModel(BaseModel):
    class meta:
        flags = ModelFlags.v2
        model_type = ModelType.dummy.value

    identifier: str
    source: str


class BriefModel(BaseModel):
    """
    BriefModel -> model display stage
    Model -> model gotten stage
    """
    class meta(BaseModel.meta):
        flags = BaseModel.meta.flags | ModelFlags.brief

    exists: ModelExistence = ModelExistence.unknown


class BriefSongModel(BriefModel):
    class meta(BriefModel.meta):
        model_type = ModelType.song

    title: str = ''
    artists_name: str = ''
    album_name: str = ''
    durtion_ms: str = ''


class SongModel(BaseModel):
    title: str
    album: Optional[Any]
    artists: List[Any]
    duration: int
    url: str

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
