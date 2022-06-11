from typing import runtime_checkable, Protocol, List, Tuple, Optional, Dict, Any
from abc import abstractmethod

from feeluown.media import Quality, Media
from .models import LyricModel, SongModel, VideoModel, ModelType
from .model_protocol import BriefSongProtocol
from .flags import Flags as PF


ID = str


FlagProtocolMapping: Dict[Tuple[ModelType, PF], type] = {}


def eq(model_type: ModelType, flag: PF):
    """Decorate a protocol class and associate it with a provider flag"""
    def wrapper(cls):
        FlagProtocolMapping[(model_type, flag)] = cls
        return cls
    return wrapper


@eq(ModelType.song, PF.get)
@runtime_checkable
class SupportsSongGet(Protocol):
    @abstractmethod
    def song_get(self, identifier: ID) -> SongModel:
        raise NotImplementedError


@eq(ModelType.song, PF.similar)
@runtime_checkable
class SupportsSongSimilar(Protocol):
    @abstractmethod
    def song_list_similar(self, identifier: ID) -> List[BriefSongProtocol]:
        raise NotImplementedError


@eq(ModelType.song, PF.multi_quality)
@runtime_checkable
class SupportsSongMultiQuality(Protocol):
    @abstractmethod
    def song_list_quality(self, identifier: ID) -> List[Quality.Audio]:
        raise NotImplementedError

    @abstractmethod
    def song_select_media(self, identifier: ID) -> Tuple[Media, Quality.Audio]:
        raise NotImplementedError

    @abstractmethod
    def song_get_media(self, identifier: ID) -> List[Quality.Audio]:
        raise NotImplementedError


@eq(ModelType.song, PF.hot_comments)
@runtime_checkable
class SupportsSongHotComments(Protocol):
    def song_list_hot_comments(self, song) -> List[SongModel]:
        raise NotImplementedError


@eq(ModelType.song, PF.web_url)
@runtime_checkable
class SupportsSongWebUrl(Protocol):
    def song_get_web_url(self, song) -> str:
        raise NotImplementedError


@eq(ModelType.song, PF.lyric)
@runtime_checkable
class SupportsSongLyric(Protocol):
    def song_get_lyric(self, song) -> Optional[LyricModel]:
        raise NotImplementedError


@eq(ModelType.song, PF.mv)
@runtime_checkable
class SupportsSongMV(Protocol):
    def song_get_mv(self, song) -> Optional[VideoModel]:
        raise NotImplementedError
