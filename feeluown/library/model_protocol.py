from typing import runtime_checkable, Optional, List, Any

from feeluown.utils.typing_ import Protocol


@runtime_checkable
class ModelProtocol(Protocol):
    """Protocol are used for typing"""
    identifier: str
    source: str
    meta: Any


@runtime_checkable
class BriefSongProtocol(ModelProtocol, Protocol):
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


@runtime_checkable
class BriefVideoProtocol(ModelProtocol, Protocol):
    """
    MvModel is also a kind of VideoModel. There is no MvModel anymore.
    """
    title: str
    artists_name: str
    # Old VideoModel/MvModel does't have this field, so we give it
    # a default value.
    duration_ms: str = ''


@runtime_checkable
class BriefArtistProtocol(ModelProtocol, Protocol):
    """
    Note that the concept `artist` may be used in radio/mv/video model.
    Be careful when adding new fields.
    """
    name: str


@runtime_checkable
class BriefAlbumProtocol(ModelProtocol, Protocol):
    name: str
    artists_name: str


@runtime_checkable
class BriefUserProtocol(ModelProtocol, Protocol):
    name: str = ''


@runtime_checkable
class UserProtocol(BriefUserProtocol, Protocol):
    avatar_url: str = ''


@runtime_checkable
class SongProtocol(BriefSongProtocol, Protocol):
    album: Optional[BriefAlbumProtocol]
    artists: List[BriefArtistProtocol]
    duration: int


@runtime_checkable
class VideoProtocol(BriefVideoProtocol, Protocol):
    artists: List[BriefArtistProtocol]
    # Old VideoModel/MvModel does't have this field, so we give it
    # a default value.
    duration: int = 0
    cover: str


@runtime_checkable
class LyricProtocol(ModelProtocol, Protocol):
    """
    Comparing to v1 LyricModel, LyricProtocol does't have `song` field
    because it is never used.

    It seems BriefLyricProtocol is not needed.
    """
    content: str
    trans_content: str = ''
