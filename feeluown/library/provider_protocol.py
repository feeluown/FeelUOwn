from typing import runtime_checkable, Protocol, List, Tuple, Optional, Dict, Any
from abc import abstractmethod

from feeluown.media import Quality, Media
from .models import (
    LyricModel, SongModel, VideoModel, AlbumModel, ArtistModel, PlaylistModel,
    UserModel, ModelType,
)
from .model_protocol import (
    BriefArtistProtocol, BriefSongProtocol, BriefUserProtocol, BriefVideoProtocol,
)
from .flags import Flags as PF


ID = str
_FlagProtocolMapping: Dict[Tuple[ModelType, PF], type] = {}


def check_flag(provider, model_type: ModelType, flag: PF) -> bool:
    """Check if provider supports X"""
    protocol_cls = _FlagProtocolMapping[(model_type, flag)]
    return isinstance(provider, protocol_cls)


def is_supported(provider, protocol):
    """Check if provider supports X"""
    return isinstance(provider, protocol)


def eq(model_type: ModelType, flag: PF):
    """Decorate a protocol class and associate it with a provider flag"""
    def wrapper(cls):
        _FlagProtocolMapping[(model_type, flag)] = cls
        return cls
    return wrapper


#
# Protocols for Song related functions.
#

@eq(ModelType.song, PF.get)
@runtime_checkable
class SupportsSongGet(Protocol):
    @abstractmethod
    def song_get(self, identifier: ID) -> SongModel:
        """
        :raises ModelNotFound: identifier is invalid
        """
        raise NotImplementedError


@eq(ModelType.song, PF.similar)
@runtime_checkable
class SupportsSongSimilar(Protocol):
    @abstractmethod
    def song_list_similar(self, identifier: ID) -> List[BriefSongProtocol]:
        """List similar songs
        """
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
    def song_get_media(self, identifier: ID) -> Optional[Media]:
        """
        :return: when quality is not valid, return None
        """
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


#
# Protocols for Album related functions.
#

@eq(ModelType.album, PF.get)
@runtime_checkable
class SupportsAlbumGet(Protocol):
    @abstractmethod
    def album_get(self, identifier: ID) -> AlbumModel:
        raise NotImplementedError


#
# Protocols for Album related functions.
#

@eq(ModelType.artist, PF.get)
@runtime_checkable
class SupportsArtistGet(Protocol):
    @abstractmethod
    def artist_get(self, identifier: ID) -> ArtistModel:
        raise NotImplementedError


@eq(ModelType.artist, PF.songs_rd)
@runtime_checkable
class SupportsArtistSongsReader(Protocol):
    @abstractmethod
    def artist_create_songs_rd(self, artist: BriefArtistProtocol):
        raise NotImplementedError


@eq(ModelType.artist, PF.songs_rd)
@runtime_checkable
class SupportsArtistAlbumsReader(Protocol):
    @abstractmethod
    def artist_create_albums_rd(self, artist: BriefArtistProtocol):
        raise NotImplementedError


#
# Protocols for Video related functions.
#

@eq(ModelType.video, PF.get)
@runtime_checkable
class SupportsVideoGet(Protocol):
    @abstractmethod
    def video_get(self, identifier: ID) -> VideoModel:
        raise NotImplementedError


@eq(ModelType.video, PF.multi_quality)
@runtime_checkable
class SupportsVideoMultiQuality(Protocol):
    @abstractmethod
    def video_list_quality(self, video: BriefVideoProtocol) -> List[Quality.Video]:
        raise NotImplementedError

    @abstractmethod
    def video_select_media(
            self, video: BriefVideoProtocol, policy=None) -> Tuple[Media, Quality.Video]:
        raise NotImplementedError

    @abstractmethod
    def video_get_media(self, video: BriefVideoProtocol, quality) -> Optional[Media]:
        raise NotImplementedError


#
# Protocols for Album related functions.
#

@eq(ModelType.playlist, PF.get)
@runtime_checkable
class SupportsPlaylistGet(Protocol):
    @abstractmethod
    def playlist_get(self, identifier: ID) -> PlaylistModel:
        raise NotImplementedError


@eq(ModelType.playlist, PF.songs_rd)
@runtime_checkable
class SupportsPlaylistSongsReader(Protocol):
    @abstractmethod
    def playlist_create_songs_rd(self, playlist):
        raise NotImplementedError


@eq(ModelType.playlist, PF.add_song)
@runtime_checkable
class SupportsPlaylistAddSong(Protocol):
    @abstractmethod
    def playlist_add_song(self, playlist, song) -> bool:
        raise NotImplementedError


@eq(ModelType.playlist, PF.remove_song)
@runtime_checkable
class SupportsPlaylistRemoveSong(Protocol):
    @abstractmethod
    def playlist_remove_song(self, playlist, song) -> bool:
        raise NotImplementedError


#
# Protocols for None related functions.
#
@eq(ModelType.none, PF.current_user)
@runtime_checkable
class SupportsCurrentUser(Protocol):
    @abstractmethod
    def has_current_user(self) -> bool:
        """Check if there is a logged in user."""

    @abstractmethod
    def get_current_user(self) -> UserModel:
        """Get current logged in user

        :raises NoUserLoggedIn: there is no logged in user.
        """
