# mypy: disable-error-code=type-abstract
import logging
import warnings
from functools import partial
from typing import cast, Optional, Union, TypeVar, Type, Callable, Any

from feeluown.media import Media
from feeluown.utils import aio
from feeluown.utils.dispatch import Signal
from feeluown.utils.reader import create_reader
from .base import SearchType, ModelType
from .provider import AbstractProvider
from .provider_v2 import ProviderV2
from .excs import (
    NotSupported, MediaNotFound, NoUserLoggedIn, ProviderAlreadyExists,
    ProviderNotFound, ModelNotFound, ResourceNotFound
)
from .flags import Flags as PF
from .models import (
    ModelFlags as MF, BriefSongModel, UserModel,
)
from .model_protocol import (
    BriefVideoProtocol, ModelProtocol, BriefSongProtocol, SongProtocol, UserProtocol,
    LyricProtocol, VideoProtocol, BriefAlbumProtocol, BriefArtistProtocol
)
from .model_state import ModelState
from .provider_protocol import (
    check_flag as check_flag_impl,
    SupportsCurrentUser, SupportsAlbumSongsReader,
    SupportsSongLyric, SupportsSongMV, SupportsSongMultiQuality,
    SupportsPlaylistRemoveSong, SupportsPlaylistAddSong, SupportsPlaylistSongsReader,
    SupportsArtistSongsReader, SupportsArtistAlbumsReader,
    SupportsVideoMultiQuality, SupportsArtistContributedAlbumsReader,
)


logger = logging.getLogger(__name__)

FULL_SCORE = 10
MIN_SCORE = 5
T_p = TypeVar('T_p')


def raise_(e):
    raise e


def support_or_raise(provider, protocol_cls):
    if not isinstance(provider, protocol_cls):
        raise NotSupported(f'{provider} not support {protocol_cls}') from None


def default_score_fn(origin, standby):

    # TODO: move this function to utils module
    def duration_ms_to_duration(ms):
        if not ms:  # ms is empty
            return 0
        m, s = ms.split(':')
        return int(m) * 60 + int(s)

    score = FULL_SCORE
    if origin.artists_name_display != standby.artists_name_display:
        score -= 3
    if origin.title_display != standby.title_display:
        score -= 2
    if origin.album_name_display != standby.album_name_display:
        score -= 2

    origin_duration = duration_ms_to_duration(origin.duration_ms_display)
    standby_duration = duration_ms_to_duration(standby.duration_ms_display)
    if abs(origin_duration - standby_duration) / max(origin_duration, 1) > 0.1:
        score -= 3

    # Debug code for score function
    # print(f"{score}\t('{standby.title_display}', "
    #       f"'{standby.artists_name_display}', "
    #       f"'{standby.album_name_display}', "
    #       f"'{standby.duration_ms_display}')")
    return score


def _sort_song_standby(song, standby_list):
    """sort song standby list by similarity"""

    def get_score(standby):
        """
        score strategy

        1. title + album > artist
        2. artist > title > album
        """

        score = 10
        if song.artists_name_display != standby.artists_name_display:
            score -= 4
        if song.title_display != standby.title_display:
            score -= 3
        if song.album_name_display != standby.album_name_display:
            score -= 2
        return score

    sorted_standby_list = sorted(
        standby_list,
        key=lambda standby: get_score(standby),
        reverse=True
    )

    return sorted_standby_list


def _extract_and_sort_song_standby_list(song, result_g):
    standby_list = []
    for result in result_g:
        for standby in result.songs[:2]:
            standby_list.append(standby)
    sorted_standby_list = _sort_song_standby(song, standby_list)
    return sorted_standby_list


def _get_display_property_or_raise(model, attr):
    """Get property with no IO operation

    I hope we need not use this function in other module because
    it is tightly coupled with display_property.
    """
    return getattr(model, f'_display_store_{attr}')


def err_provider_not_support_flag(pid, model_type, op):
    op_str = str(op)
    if op is PF.get:
        op_str = 'get'
    mtype_str = str(ModelType(model_type))
    return NotSupported(f"provider:{pid} does't support '{op_str}' for {mtype_str}")


class Library:
    """音乐库，管理资源提供方以及资源"""

    def __init__(self, providers_standby=None):
        """

        :type app: feeluown.app.App
        """
        self._providers_standby = providers_standby
        self._providers = set()

        self.provider_added = Signal()  # emit(AbstractProvider)
        self.provider_removed = Signal()  # emit(AbstractProvider)

    def register(self, provider):
        """register provider

        :raises ProviderAlreadyExists:
        :raises ValueError:
        """
        if not isinstance(provider, AbstractProvider):
            raise ValueError('invalid provider instance')
        for _provider in self._providers:
            if _provider.identifier == provider.identifier:
                raise ProviderAlreadyExists
        self._providers.add(provider)
        self.provider_added.emit(provider)

    def deregister(self, provider):
        """deregister provider"""
        try:
            self._providers.remove(provider)
        except ValueError:
            raise ProviderNotFound from None
        else:
            self.provider_removed.emit(provider)

    def get(self, identifier):
        """通过资源提供方唯一标识获取提供方实例"""
        for provider in self._providers:
            if provider.identifier == identifier:
                return provider
        return None

    def list(self):
        """列出所有资源提供方"""
        return list(self._providers)

    def _filter(self, identifier_in=None):
        if identifier_in is None:
            return iter(self._providers)
        return filter(lambda p: p.identifier in identifier_in, self.list())

    def search(self, keyword, type_in=None, source_in=None, **kwargs):
        """search song/artist/album/playlist by keyword

        please use a_search method if you can.

        :param keyword: search keyword
        :param type_in: search type
        :param source_in: None or provider identifier list

        - TODO: support search with filters(by artist or by source)
        """
        type_in = SearchType.batch_parse(type_in) if type_in else [SearchType.so]
        for provider in self._filter(identifier_in=source_in):
            for type_ in type_in:
                try:
                    result = provider.search(keyword=keyword, type_=type_, **kwargs)
                except Exception:  # pylint: disable=broad-except
                    logger.exception('Search %s in %s failed.', keyword, provider)
                else:
                    if result is not None:
                        yield result

    async def a_search(self, keyword, source_in=None, timeout=None,
                       type_in=None,
                       **kwargs):
        """async version of search

        TODO: add Happy Eyeballs requesting strategy if needed
        """
        type_in = SearchType.batch_parse(type_in) if type_in else [SearchType.so]

        fs = []  # future list
        for provider in self._filter(identifier_in=source_in):
            for type_ in type_in:
                future = aio.run_in_executor(
                    None,
                    partial(provider.search, keyword, type_=type_))
                fs.append(future)

        for future in aio.as_completed(fs, timeout=timeout):
            try:
                result = await future
            except:  # noqa
                logger.exception('search task failed')
                continue
            else:
                # When a provider does not implement search method, it returns None.
                if result is not None:
                    yield result

    async def a_list_song_standby_v2(self, song,
                                     audio_select_policy='>>>', source_in=None,
                                     score_fn=None, min_score=MIN_SCORE, limit=1):
        """list song standbys and their media

        .. versionadded:: 3.7.8

        """

        async def prepare_media(standby, policy):
            media = None
            try:
                media = await aio.run_in_executor(None,
                                                  self.song_prepare_media,
                                                  standby, policy)
            except MediaNotFound:
                pass
            except:  # noqa
                logger.exception(f'get standby:{standby} media failed')
            return media

        if source_in is None:
            pvd_ids = self._providers_standby or [pvd.identifier for pvd in self.list()]
        else:
            pvd_ids = [pvd.identifier for pvd in self._filter(identifier_in=source_in)]
        if score_fn is None:
            score_fn = default_score_fn
        limit = max(limit, 1)

        q = '{} {}'.format(song.title_display, song.artists_name_display)
        standby_score_list = []  # [(standby, score), (standby, score)]
        song_media_list = []     # [(standby, media), (standby, media)]
        async for result in self.a_search(q, source_in=pvd_ids):
            if result is None:
                continue
            # Only check the first 3 songs
            for standby in result.songs:
                score = score_fn(song, standby)
                if score == FULL_SCORE:
                    media = await prepare_media(standby, audio_select_policy)
                    if media is None:
                        continue
                    logger.info(f'find full mark standby for song:{q}')
                    song_media_list.append((standby, media))
                    if len(song_media_list) >= limit:
                        # Return as early as possible to get better performance
                        return song_media_list
                elif score >= min_score:
                    standby_score_list.append((standby, score))
        # Limit try times since prapare_media is an expensive IO operation
        max_try = len(pvd_ids) * 2
        for standby, score in sorted(standby_score_list,
                                     key=lambda song_score: song_score[1],
                                     reverse=True)[:max_try]:
            media = await prepare_media(standby, audio_select_policy)
            if media is not None:
                song_media_list.append((standby, media))
                if len(song_media_list) >= limit:
                    return song_media_list
        return song_media_list

    #
    # methods for v2
    #

    # provider common

    def get_or_raise(self, identifier) -> Union[AbstractProvider, ProviderV2]:
        """
        :raises ProviderNotFound:
        """
        provider = self.get(identifier)
        if provider is None:
            raise ProviderNotFound(f'provider {identifier} not found')
        return provider

    def getv2_or_raise(self, identifier):
        provider = self.get_or_raise(identifier)
        # You should ensure the provider is v2 first. For example, if check_flags
        # returns true, the provider must be a v2 instance.
        assert isinstance(provider, ProviderV2), 'provider must be v2'
        return provider

    def check_flags(self, source: str, model_type: ModelType, flags: PF) -> bool:
        """Check if a provider satisfies the specific ability for a model type

        .. note::

             Currently, we use ProviderFlags to define which ability a
             provider has. In the future, we may use typing.Protocol.
             So you should use :meth:`check_flags` method to check ability
             instead of compare provider flags directly.
        """
        provider = self.get(source)
        if provider is None:
            return False

        # Check each flag.
        for value in PF.__members__.values():
            if value in PF(flags):
                if check_flag_impl(provider, model_type, flags) is False:
                    return False
        return True

    def check_flags_by_model(self, model: ModelProtocol, flags: PF) -> bool:
        """Alias for check_flags"""
        warnings.warn('please use isinstance(provider, protocol_cls)')
        return self.check_flags(model.source,
                                ModelType(model.meta.model_type),
                                flags)

    # -----
    # Songs
    # -----
    def song_upgrade(self, song: BriefSongProtocol) -> SongProtocol:
        return self._model_upgrade(song)  # type: ignore

    def song_prepare_media(self, song: BriefSongProtocol, policy) -> Media:
        provider = self.get(song.source)
        if provider is None:
            # FIXME: raise ProviderNotfound
            raise MediaNotFound(f'provider:{song.source} not found')
        if song.meta.flags & MF.v2:
            support_or_raise(provider, SupportsSongMultiQuality)
            provider = cast(SupportsSongMultiQuality, provider)
            media, _ = provider.song_select_media(song, policy)
        else:
            if song.meta.support_multi_quality:
                media, _ = song.select_media(policy)  # type: ignore
            else:
                url = song.url  # type: ignore
                if url:
                    media = Media(url)
                else:
                    raise MediaNotFound
        if not media:
            raise MediaNotFound
        return media

    def song_prepare_mv_media(self, song: BriefSongProtocol, policy) -> Media:
        """

        .. versionadded:: 3.7.5
        """
        mv = self.song_get_mv(song)
        if mv is not None:
            media = self.video_prepare_media(mv, policy)
            return media
        raise MediaNotFound

    def song_get_mv(self, song: BriefSongProtocol) -> Optional[VideoProtocol]:
        """Get the MV model of a song.

        :raises NotSupported:
        :raises ProviderNotFound:
        """
        provider = self.get_or_raise(song.source)
        if isinstance(provider, SupportsSongMV):
            mv = provider.song_get_mv(song)
        else:
            mv = None
        return mv

    def song_get_lyric(self, song: BriefSongModel) -> Optional[LyricProtocol]:
        """Get the lyric model of a song.

        Return None when lyric does not exist instead of raising exceptions,
        because it is predictable.

        :raises NotSupported:
        :raises ProviderNotFound:
        """
        provider = self.get_or_raise(song.source)
        if isinstance(provider, SupportsSongLyric):
            return provider.song_get_lyric(song)
        raise NotSupported

    def song_get_web_url(self, song: BriefSongProtocol) -> str:
        provider = self.getv2_or_raise(song.source)
        return provider.song_get_web_url(song)

    # --------
    # Album
    # --------
    def album_upgrade(self, album: BriefAlbumProtocol):
        return self._model_upgrade(album)

    def album_create_songs_rd(self, album: BriefAlbumProtocol):
        """Create songs reader for album model."""
        return self._handle_protocol_with_model(
            SupportsAlbumSongsReader,
            lambda p, m: p.album_create_songs_rd(m),
            lambda v1_m: create_reader(v1_m.songs),  # type: ignore
            album,
        )

    def _handle_protocol_with_model(self,
                                    protocol_cls: Type[T_p],
                                    v2_handler: Callable[[T_p, Any], Any],
                                    v1_handler: Callable[[Any], Any],
                                    model: ModelProtocol):
        """A handler helper (experimental).

        :raises ProviderNotFound:
        :raises NotSupported:
        """
        provider = self.get_or_raise(model.source)
        if isinstance(provider, protocol_cls):
            return v2_handler(provider, model)
        raise NotSupported(f'{protocol_cls} not supported')

    # --------
    # Artist
    # --------
    def artist_upgrade(self, artist: BriefArtistProtocol):
        return self._model_upgrade(artist)

    def artist_create_songs_rd(self, artist):
        """Create songs reader for artist model."""
        return self._handle_protocol_with_model(
            SupportsArtistSongsReader,
            lambda p, m: p.artist_create_songs_rd(m),
            lambda v1_m: (create_reader(v1_m.create_songs_g())
                          if v1_m.meta.allow_create_songs_g else
                          create_reader(v1_m.songs)),
            artist,
        )

    def artist_create_albums_rd(self, artist, contributed=False):
        """Create albums reader for artist model."""
        source = artist.source
        if contributed is False:
            protocol_cls = SupportsArtistAlbumsReader
            return self._handle_protocol_with_model(
                protocol_cls,
                lambda p, m: p.artist_create_albums_rd(m),
                lambda v1_m: (create_reader(v1_m.create_albums_g())
                              if v1_m.meta.allow_create_albums_g else
                              raise_(NotSupported.create_by_p_p(source, protocol_cls))),
                artist
            )
        protocol_cls = SupportsArtistContributedAlbumsReader
        return self._handle_protocol_with_model(
            protocol_cls,
            lambda p, m: p.artist_create_contributed_albums_rd(m),
            # Old code check if provider supports contributed_albums in this way,
            # have to say, it is a little ugly.
            lambda v1_m: (
                create_reader(v1_m.create_contributed_albums_g())
                if hasattr(v1_m, 'contributed_albums') and v1_m.contributed_albums else
                raise_(NotSupported.create_by_p_p(source, protocol_cls))
            ),
            artist
        )

    # --------
    # Playlist
    # --------

    def playlist_upgrade(self, playlist):
        return self._model_upgrade(playlist)

    def playlist_create_songs_rd(self, playlist):
        """Create songs reader for artist model."""
        return self._handle_protocol_with_model(
            SupportsPlaylistSongsReader,
            lambda p, m: p.playlist_create_songs_rd(m),
            lambda v1_m: (create_reader(v1_m.create_songs_g())
                          if v1_m.meta.allow_create_songs_g else
                          create_reader(v1_m.songs)),
            playlist,
        )

    def playlist_remove_song(self, playlist, song) -> bool:
        """Remove a song from the playlist

        :return: true if the song is not in playlist anymore.
        """
        provider = self.get_or_raise(playlist.source)
        if isinstance(provider, SupportsPlaylistRemoveSong):
            return provider.playlist_remove_song(playlist, song)
        raise NotSupported

    def playlist_add_song(self, playlist, song) -> bool:
        """Add a song to the playlist

        :return: true if the song exists in playlist.
        """
        provider = self.get_or_raise(playlist.source)
        if isinstance(provider, SupportsPlaylistAddSong):
            return provider.playlist_add_song(playlist, song)
        raise NotSupported

    # -------------------------
    # generic methods for model
    # -------------------------
    def model_get(self, pid, mtype, mid):
        """Get a (normal) model instance.

        :param pid: provider id
        :param mtype: model type
        :param mid: model id
        :return: model

        :raise NotSupported: provider has not .get for this model type
        :raise ResourceNotFound: model does not exist
        """
        provider = self.get_or_raise(pid)
        model = None
        try_v1way = True
        if isinstance(provider, ProviderV2):
            if provider.use_model_v2(mtype):
                if self.check_flags(pid, mtype, PF.get):
                    try_v1way = False
                    model = provider.model_get(mtype, mid)

        # Try to use the ModelV1.get API to get the model.
        if try_v1way and isinstance(provider, AbstractProvider):
            try:
                model_cls = provider.get_model_cls(mtype)
                model = model_cls.get(mid)
            except AttributeError:
                pass
        if model is None:
            raise ModelNotFound
        return model

    def model_get_cover(self, model):
        """Get the cover url of model

        :param model: model which has a 'cover' field.
        :return: cover url if exists, else ''.
        """
        if MF.v2 in model.meta.flags:
            if MF.normal not in model.meta.flags:
                try:
                    um = self._model_upgrade(model)
                except (ResourceNotFound, NotSupported):
                    return ''
            else:
                um = model
            # FIXME: remove this hack lator.
            if ModelType(model.meta.model_type) is ModelType.artist:
                cover = um.pic_url
            else:
                cover = um.cover
        else:
            cover = model.cover
            # Check if cover is a media object.
            if cover and not isinstance(cover, str):
                cover = cover.url
        return cover

    def _model_upgrade(self, model):
        """Upgrade a model to normal model.

        :raises NotSupported: provider does't impl SupportGetProtocol for the model type
        :raises ModelNotFound: the model does not exist
        :raises ProviderNotFound: the provider does not exist

        Note you may catch ResourceNotFound exception to simplify your code.

        .. versionchanged:: 3.8.11
            Raise ModelNotFound if the model does not exist.
            Before ModelCannotUpgrade was raised.
        """
        # Upgrade model in v1 way if it is a v1 model.
        if MF.v2 not in model.meta.flags:
            return self._model_upgrade_in_v1_way(model)

        # Return model directly if it is already a normal model.
        if MF.normal in model.meta.flags:
            return model

        provider = self.getv2_or_raise(model.source)
        model_type = ModelType(model.meta.model_type)
        is_support = check_flag_impl(provider, model_type, PF.get)
        if is_support:
            try:
                upgraded_model = provider.model_get(model_type, model.identifier)
            except ModelNotFound:
                model.state = ModelState.not_exists
                raise
            else:
                # Provider should raise ModelNotFound when the mode does not exist.
                # Some providers does not follow the protocol, and they may return None.
                # Keep this logic to keep backward compatibility.
                if upgraded_model is None:
                    model.state = ModelState.not_exists
                    raise ModelNotFound(f'provider:{provider} return an empty model')
                return upgraded_model
        raise NotSupported

    # --------
    # Video
    # --------
    def video_upgrade(self, video):
        return self._model_upgrade(video)

    def video_prepare_media(self, video: BriefVideoProtocol, policy) -> Media:
        """Prepare media for video.

        :param video: either a v1 MvModel or a v2 (Brief)VideoModel.
        """
        provider = self.get_or_raise(video.source)
        if video.meta.flags & MF.v2:
            # provider MUST has multi_quality flag for video
            assert isinstance(provider, SupportsVideoMultiQuality)
            media, _ = provider.video_select_media(video, policy)
        else:
            # V1 VideoModel has attribute `media`
            if video.meta.support_multi_quality:
                media, _ = video.select_media(policy)  # type: ignore
            else:
                media = video.media  # type: ignore
        if not media:
            raise MediaNotFound
        return media

    # --------
    # Provider
    # --------
    def provider_has_current_user(self, source: str) -> bool:
        """Check if a provider has a logged in user

        No IO operation is triggered.

        .. versionadded:: 3.7.6
        """
        provider = self.get_or_raise(source)
        if isinstance(provider, SupportsCurrentUser):
            return provider.has_current_user()

        try:
            user_v1 = getattr(provider, '_user')
        except AttributeError:
            logger.warn("We can't determine if the provider has a current user")
            return False
        else:
            return user_v1 is not None

    def provider_get_current_user(self, source: str) -> UserProtocol:
        """Get provider current logged in user

        :raises NotSupported:
        :raises ProviderNotFound:
        :raises NoUserLoggedIn:

        .. versionadded:: 3.7.6
        """
        provider = self.get_or_raise(source)
        if isinstance(provider, SupportsCurrentUser):
            return provider.get_current_user()

        user_v1 = getattr(provider, '_user', None)
        if user_v1 is None:
            raise NoUserLoggedIn
        return UserModel(identifier=user_v1.identifier,
                         source=source,
                         name=user_v1.name_display,
                         avatar_url='')
