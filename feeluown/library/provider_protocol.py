from typing import runtime_checkable, Protocol, List, Tuple, Optional, Dict
from abc import abstractmethod
from feeluown.media import Quality, Media
from .models import (
    BriefCommentModel, SongModel, VideoModel, AlbumModel, ArtistModel,
    PlaylistModel, UserModel, ModelType,
)
from .model_protocol import (
    BriefArtistProtocol, BriefSongProtocol, SongProtocol,
    BriefVideoProtocol, VideoProtocol,
    LyricProtocol,
)
from .flags import Flags as PF


ID = str
_FlagProtocolMapping: Dict[Tuple[ModelType, PF], type] = {}


def check_flag(provider, model_type: ModelType, flag: PF) -> bool:
    """Check if provider supports X"""

    # A provider should declare explicitly whether it uses model v2 or not.
    if flag is PF.model_v2:
        try:
            use_model_v2 = provider.use_model_v2(model_type)
        except AttributeError:  # noqa
            # The provider may not implement the `use_model_v2` interface.
            return False
        return use_model_v2

    protocol_cls = _FlagProtocolMapping[(model_type, flag)]
    return isinstance(provider, protocol_cls)


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
        :raises ModelNotFound: model not found by the identifier
        :raises ProviderIOError:
        """
        raise NotImplementedError


@eq(ModelType.song, PF.similar)
@runtime_checkable
class SupportsSongSimilar(Protocol):
    @abstractmethod
    def song_list_similar(self, song: BriefSongProtocol) -> List[BriefSongProtocol]:
        """List similar songs
        """
        raise NotImplementedError


@eq(ModelType.song, PF.multi_quality)
@runtime_checkable
class SupportsSongMultiQuality(Protocol):
    @abstractmethod
    def song_list_quality(self, song: BriefSongProtocol) -> List[Quality.Audio]:
        """List all possible qualities

        Please ensure all the qualities are valid. `song_get_media(song, quality)`
        must not return None with a valid quality.
        """
        raise NotImplementedError

    @abstractmethod
    def song_select_media(
        self, song: BriefSongProtocol, policy=None
    ) -> Tuple[Media, Quality.Audio]:
        """Select a media by the quality sorting policy

        If the song has some valid medias, this method can always return one of them.
        """
        raise NotImplementedError

    @abstractmethod
    def song_get_media(
        self, song: BriefVideoProtocol, quality: Quality.Audio
    ) -> Optional[Media]:
        """Get song's media by a specified quality

        :return: when quality is invalid, return None
        """
        raise NotImplementedError


@eq(ModelType.song, PF.hot_comments)
@runtime_checkable
class SupportsSongHotComments(Protocol):
    def song_list_hot_comments(self, song: BriefSongProtocol) -> List[BriefCommentModel]:
        raise NotImplementedError


@eq(ModelType.song, PF.web_url)
@runtime_checkable
class SupportsSongWebUrl(Protocol):
    def song_get_web_url(self, song: BriefSongProtocol) -> str:
        raise NotImplementedError


@eq(ModelType.song, PF.lyric)
@runtime_checkable
class SupportsSongLyric(Protocol):
    def song_get_lyric(self, song: BriefSongProtocol) -> Optional[LyricProtocol]:
        """Get music video of the song
        """
        raise NotImplementedError


@eq(ModelType.song, PF.mv)
@runtime_checkable
class SupportsSongMV(Protocol):
    def song_get_mv(self, song: BriefSongProtocol) -> Optional[VideoProtocol]:
        """Get music video of the song

        """
        raise NotImplementedError


#
# Protocols for Album related functions.
#

@eq(ModelType.album, PF.get)
@runtime_checkable
class SupportsAlbumGet(Protocol):
    @abstractmethod
    def album_get(self, identifier: ID) -> AlbumModel:
        """
        :raises ModelNotFound: model not found by the identifier
        :raises ProviderIOError:
        """
        raise NotImplementedError


@eq(ModelType.album, PF.songs_rd)
@runtime_checkable
class SupportsAlbumSongsReader(Protocol):
    @abstractmethod
    def album_create_songs_rd(self, album) -> List[SongProtocol]:
        raise NotImplementedError


#
# Protocols for Album related functions.
#

@eq(ModelType.artist, PF.get)
@runtime_checkable
class SupportsArtistGet(Protocol):
    @abstractmethod
    def artist_get(self, identifier: ID) -> ArtistModel:
        """
        :raises ModelNotFound: model not found by the identifier
        :raises ProviderIOError:
        """
        raise NotImplementedError


@eq(ModelType.artist, PF.songs_rd)
@runtime_checkable
class SupportsArtistSongsReader(Protocol):
    @abstractmethod
    def artist_create_songs_rd(self, artist: BriefArtistProtocol):
        """Create songs reader of the artist
        """
        raise NotImplementedError


@eq(ModelType.artist, PF.albums_rd)
@runtime_checkable
class SupportsArtistAlbumsReader(Protocol):
    @abstractmethod
    def artist_create_albums_rd(self, artist: BriefArtistProtocol):
        """Create albums reader of the artist
        """
        raise NotImplementedError


@runtime_checkable
class SupportsArtistContributedAlbumsReader(Protocol):
    @abstractmethod
    def artist_create_contributed_albums_rd(self, artist: BriefArtistProtocol):
        """Create contributed albums reader of the artist
        """
        raise NotImplementedError


#
# Protocols for Video related functions.
#

@eq(ModelType.video, PF.get)
@runtime_checkable
class SupportsVideoGet(Protocol):
    @abstractmethod
    def video_get(self, identifier: ID) -> VideoModel:
        """
        :raises ModelNotFound: model not found by the identifier
        :raises ProviderIOError:
        """
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
        """
        :raises ModelNotFound: model not found by the identifier
        :raises ProviderIOError:
        """
        raise NotImplementedError


@runtime_checkable
class SupportsPlaylistCreateByName(Protocol):
    @abstractmethod
    def playlist_create_by_name(self, name) -> PlaylistModel:
        """Create playlist for user logged in.

        :raises NoUserLoggedIn:
        :raises ProviderIOError:
        """


@runtime_checkable
class SupportsPlaylistDelete(Protocol):
    @abstractmethod
    def playlist_delete(self, identifier: ID) -> bool:
        """
        :raises ModelNotFound: model not found by the identifier
        :raises ProviderIOError:
        """
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


@runtime_checkable
class SupportsCurrentUserListPlaylists(Protocol):
    @abstractmethod
    def current_user_list_playlists(self):
        """
        : raises NoUserLoggedIn:
        """


#
# Protocols for current user favorites/collections
#
@runtime_checkable
class SupportsCurrentUserFavSongsReader(Protocol):
    @abstractmethod
    def current_user_fav_create_songs_rd(self):
        """
        : raises NoUserLoggedIn:
        """


@runtime_checkable
class SupportsCurrentUserFavAlbumsReader(Protocol):
    @abstractmethod
    def current_user_fav_create_albums_rd(self):
        pass


@runtime_checkable
class SupportsCurrentUserFavArtistsReader(Protocol):
    @abstractmethod
    def current_user_fav_create_artists_rd(self):
        pass


@runtime_checkable
class SupportsCurrentUserFavPlaylistsReader(Protocol):
    @abstractmethod
    def current_user_fav_create_playlists_rd(self):
        pass


@runtime_checkable
class SupportsCurrentUserFavVideosReader(Protocol):
    @abstractmethod
    def current_user_fav_create_videos_rd(self):
        pass


#
# Protocols for recommendation.
#
@runtime_checkable
class SupportsRecListDailySongs(Protocol):
    @abstractmethod
    def rec_list_daily_songs(self) -> List[SongModel]:
        pass


@runtime_checkable
class SupportsRecListDailyPlaylists(Protocol):
    @abstractmethod
    def rec_list_daily_playlists(self) -> List[PlaylistModel]:
        pass


@runtime_checkable
class SupportsRecListDailyAlbums(Protocol):
    @abstractmethod
    def rec_list_daily_albums(self) -> List[AlbumModel]:
        pass
