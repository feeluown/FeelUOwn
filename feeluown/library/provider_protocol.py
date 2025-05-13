from typing import runtime_checkable, Protocol, List, Tuple, Optional, Dict
from abc import abstractmethod
from feeluown.media import Quality, Media
from feeluown.excs import NoUserLoggedIn
from feeluown.utils.dispatch import Signal
from .models import (
    BriefCommentModel, SongModel, VideoModel, AlbumModel, ArtistModel,
    PlaylistModel, UserModel, ModelType, BriefArtistModel, BriefSongModel,
    LyricModel, BriefVideoModel, BriefPlaylistModel,
)
from .collection import Collection

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
    def song_list_similar(self, song: BriefSongModel) -> List[BriefSongModel]:
        """List similar songs
        """
        raise NotImplementedError


@eq(ModelType.song, PF.multi_quality)
@runtime_checkable
class SupportsSongMultiQuality(Protocol):
    @abstractmethod
    def song_list_quality(self, song: BriefSongModel) -> List[Quality.Audio]:
        """List all possible qualities

        Please ensure all the qualities are valid. `song_get_media(song, quality)`
        must not return None with a valid quality.
        """
        raise NotImplementedError

    @abstractmethod
    def song_select_media(
        self, song: BriefSongModel, policy=None
    ) -> Tuple[Media, Quality.Audio]:
        """Select a media by the quality sorting policy

        If the song has some valid medias, this method can always return one of them.
        """
        raise NotImplementedError

    @abstractmethod
    def song_get_media(
        self, song: BriefVideoModel, quality: Quality.Audio
    ) -> Optional[Media]:
        """Get song's media by a specified quality

        :return: when quality is invalid, return None
        """
        raise NotImplementedError


@eq(ModelType.song, PF.hot_comments)
@runtime_checkable
class SupportsSongHotComments(Protocol):
    def song_list_hot_comments(self, song: BriefSongModel) -> List[BriefCommentModel]:
        raise NotImplementedError


@eq(ModelType.song, PF.web_url)
@runtime_checkable
class SupportsSongWebUrl(Protocol):
    def song_get_web_url(self, song: BriefSongModel) -> str:
        raise NotImplementedError


@eq(ModelType.song, PF.lyric)
@runtime_checkable
class SupportsSongLyric(Protocol):
    def song_get_lyric(self, song: BriefSongModel) -> Optional[LyricModel]:
        """Get music video of the song
        """
        raise NotImplementedError


@eq(ModelType.song, PF.mv)
@runtime_checkable
class SupportsSongMV(Protocol):
    def song_get_mv(self, song: BriefSongModel) -> Optional[VideoModel]:
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
    def album_create_songs_rd(self, album) -> List[SongModel]:
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
    def artist_create_songs_rd(self, artist: BriefArtistModel):
        """Create songs reader of the artist
        """
        raise NotImplementedError


@eq(ModelType.artist, PF.albums_rd)
@runtime_checkable
class SupportsArtistAlbumsReader(Protocol):
    @abstractmethod
    def artist_create_albums_rd(self, artist: BriefArtistModel):
        """Create albums reader of the artist
        """
        raise NotImplementedError


@runtime_checkable
class SupportsArtistContributedAlbumsReader(Protocol):
    @abstractmethod
    def artist_create_contributed_albums_rd(self, artist: BriefArtistModel):
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


@runtime_checkable
class SupportsVideoWebUrl(Protocol):
    def video_get_web_url(self, video: BriefVideoModel) -> str:
        raise NotImplementedError


@eq(ModelType.video, PF.multi_quality)
@runtime_checkable
class SupportsVideoMultiQuality(Protocol):
    @abstractmethod
    def video_list_quality(self, video: BriefVideoModel) -> List[Quality.Video]:
        raise NotImplementedError

    @abstractmethod
    def video_select_media(
            self, video: BriefVideoModel, policy=None) -> Tuple[Media, Quality.Video]:
        raise NotImplementedError

    @abstractmethod
    def video_get_media(self, video: BriefVideoModel, quality) -> Optional[Media]:
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

        .. versionchanged: 4.0
            It can return Optional[UserModel], NoUserLoggedIn makes no sense.
        """

    def get_current_user_or_none(self) -> Optional[UserModel]:
        """
        .. versionadded: 4.0
        """
        try:
            return self.get_current_user()
        except NoUserLoggedIn:
            return None


@runtime_checkable
class SupportsUserAutoLogin(Protocol):
    """Protocol for providers that support automatic login using cached credentials."""

    @abstractmethod
    def auto_login(self) -> bool:
        """Try to automatically login using cached credentials.

        Returns:
            bool: True if auto login succeeded, False otherwise
        """


@runtime_checkable
class SupportsCurrentUserChanged(Protocol):
    @property
    @abstractmethod
    def current_user_changed(self) -> Signal:
        """

        :return: Signal(UserModel)
        """
        ...


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


@runtime_checkable
class SupportsCurrentUserDislikeSongsReader(Protocol):
    """Support reading the song dislike list."""
    @abstractmethod
    def current_user_dislike_create_songs_rd(self) -> List[BriefSongModel]:
        pass


@runtime_checkable
class SupportsCurrentUserDislikeAddSong(Protocol):
    """Support adding a song to the song dislike list."""
    @abstractmethod
    def current_user_dislike_add_song(self, song: BriefSongModel) -> bool:
        """
        :return: True if the song is added to the dislike list, False otherwise.
        """


@runtime_checkable
class SupportsCurrentUserDislikeRemoveSong(Protocol):
    """Support removing a song from the song dislike list."""
    @abstractmethod
    def current_user_dislike_remove_song(self, song: BriefSongModel) -> bool:
        """
        :return: True if the song is removed from the dislike list, False otherwise.
        """


@runtime_checkable
class SupportsToplist(Protocol):
    @abstractmethod
    def toplist_list(self) -> List[BriefPlaylistModel]:
        """List all toplist(排行榜)."""

    @abstractmethod
    def toplist_get(self, toplist_id) -> PlaylistModel:
        """Get toplist details.

        For some providers, the toplist model(schema) may be different from the
        PlaylistModel. They should think about a way to solve this. For example,
        turn the identifier into `toplist_{id}` and do some hack in playlist_get API.
        """


#
# Protocols for recommendation.
#
@runtime_checkable
class SupportsRecListDailySongs(Protocol):
    @abstractmethod
    def rec_list_daily_songs(self) -> List[SongModel]:
        pass


@runtime_checkable
class SupportsRecACollectionOfSongs(Protocol):
    @abstractmethod
    def rec_a_collection_of_songs(self) -> Collection:
        """
        For example, providers may provider a list of songs,
        and the title looks like “大家都在听” / “红心歌曲”.

        For different user, this API may return different result.
        """


@runtime_checkable
class SupportsRecACollectionOfVideos(Protocol):
    @abstractmethod
    def rec_a_collection_of_videos(self) -> Collection:
        """
        For example, providers may recommend a list of videos.
        For different user, this API may return different result.
        This API MAY return different result at different time.
        """


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
