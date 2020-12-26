from typing import Optional, List, Any

from feeluown.utils.typing_ import Protocol
from .model_state import ModelState


class ModelProtocol(Protocol):
    """Protocol are used for typing"""
    identifier: str
    source: str
    state: ModelState
    meta: Any


class BriefSongProtocol(ModelProtocol):
    """
    We want to have such kind of check in code::

        brief_song = BriefSongModel(...)
        song = SongModel(...)
        isinstance(brief_song, BriefSongModel) -> True
        isinstance(song, BriefSongModel) -> True

    Due to pydantic mechanism, SongModel should not inherit from BriefSongModel
    because BriefSongModel define `duration_ms/title/...` as Model fields. Model
    fields can be get and set. In SongModel, these fields is only supposed to be get.
    As a result `isinstance(song, BriefSongModel)` returns False.

    We define this protocol to solve this problem. We can some check in this way::

        brief_song = BriefSongModel(...)
        song = SongModel(...)
        isinstance(brief_song, BriefSongProtocol) -> True
        isinstance(song, BriefSongProtocol) -> True

        isinstance(song, SongModel) -> True

    Considering the backward compatibility of v1 model. We define SongProtocol
    for SongModel and v1 SongModel. So we can have following code::

        isinstance(old_song, SongProtocol) -> True
        isinstance(song, SongProtocol) -> True
    """
    title: str
    artists_name: str
    album_name: str
    duration_ms: str


class BriefArtistProtocol(ModelProtocol):
    name: str


class BriefAlbumProtocol(ModelProtocol):
    name: str
    artists_name: str


class SongProtocol(BriefSongProtocol):
    """
    Actually, Song has much more attributes(disc/gene/date), so we may want to
    extend SongProtocol in the future. I have an idea currently. We can define
    SongExtMetaProtocol/SongExtXxxProtocol to extend SongProtocol.
    """
    album: Optional[BriefAlbumProtocol]
    artists: List[BriefArtistProtocol]
    duration: int
