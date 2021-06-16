import logging
from functools import partial, lru_cache
from typing import List, cast

from feeluown.utils import aio
from feeluown.utils.dispatch import Signal
from feeluown.media import Media
from feeluown.models import SearchType, ModelType
from feeluown.utils.utils import log_exectime
from .provider import AbstractProvider
from .provider_v2 import ProviderV2
from .excs import (
    NotSupported, MediaNotFound, NoUserLoggedIn, ProviderAlreadyExists,
    ProviderNotFound,
)
from .flags import Flags as PF
from .models import (
    ModelFlags as MF, BaseModel, BriefSongModel, SongModel, UserModel,
)
from .model_protocol import (
    ModelProtocol, BriefSongProtocol, SongProtocol, UserProtocol,
)


logger = logging.getLogger(__name__)


FULL_SCORE = 10
MIN_SCORE = 5


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

        >>> from feeluown.library import dummy_provider
        >>> library = Library(None)
        >>> library.register(dummy_provider)
        >>> library.register(dummy_provider)
        Traceback (most recent call last):
            ...
        feeluown.library.excs.ProviderAlreadyExists
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
                yield result

    @log_exectime
    def list_song_standby(self, song, onlyone=True):
        """try to list all valid standby

        Search a song in all providers. The typical usage scenario is when a
        song is not available in one provider, we can try to acquire it from other
        providers.

        FIXME: this method will send several network requests,
        which may block the caller.

        :param song: song model
        :param onlyone: return only one element in result
        :return: list of songs (maximum count: 2)
        """
        valid_sources = [pvd.identifier for pvd in self.list()
                         if pvd.identifier != song.source]
        q = '{} {}'.format(song.title, song.artists_name)
        result_g = self.search(q, source_in=valid_sources)
        sorted_standby_list = _extract_and_sort_song_standby_list(song, result_g)
        # choose one or two valid standby
        result = []
        for standby in sorted_standby_list:
            if standby.url:  # this may trigger network request
                result.append(standby)
                if onlyone or len(result) >= 2:
                    break
        return result

    async def a_list_song_standby(self, song, onlyone=True, source_in=None):
        """async version of list_song_standby

        .. versionadded:: 3.7.5
             The *source_in* paramter.
        """
        if source_in is None:
            pvd_ids = self._providers_standby or [pvd.identifier for pvd in self.list()]
        else:
            pvd_ids = [pvd.identifier for pvd in self._filter(identifier_in=source_in)]
        # FIXME(cosven): the model return from netease is new model,
        # and it does not has url attribute
        valid_providers = [pvd_id for pvd_id in pvd_ids
                           if pvd_id != song.source and pvd_id != 'netease']
        q = '{} {}'.format(song.title_display, song.artists_name_display)
        result_g = []
        async for result in self.a_search(q, source_in=valid_providers):
            if result is not None:
                result_g.append(result)
        sorted_standby_list = _extract_and_sort_song_standby_list(song, result_g)
        # choose one or two valid standby
        result = []
        for standby in sorted_standby_list:
            try:
                url = await aio.run_in_executor(None, lambda: standby.url)
            except:  # noqa
                logger.exception('get standby url failed')
            else:
                if url:
                    result.append(standby)
                    if onlyone or len(result) >= 2:
                        break
        return result

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

    def get_or_raise(self, identifier) -> ProviderV2:
        """
        :raises ProviderNotFound:
        """
        provider = self.get(identifier)
        if provider is None:
            raise ProviderNotFound(f'provider {identifier} not found')
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
        if isinstance(provider, ProviderV2):
            return provider.check_flags(model_type, flags)
        return False

    def check_flags_by_model(self, model: ModelProtocol, flags: PF) -> bool:
        """Alias for check_flags"""
        return self.check_flags(model.source,
                                ModelType(model.meta.model_type),
                                flags)

    # ---------------------------
    # Methods for backward compat
    # ---------------------------
    def cast_model_to_v1(self, model):
        """Cast a v1/v2 model to v1

        During the model migration from v1 to v2, v2 may lack some ability.
        Cast the model to v1 to acquire such ability.
        """
        if isinstance(model, BaseModel) and (model.meta.flags & MF.v2):
            return self._cast_model_to_v1_impl(model)
        return model

    @lru_cache(maxsize=1024)
    def _cast_model_to_v1_impl(self, model):
        provider = self.get_or_raise(model.source)
        ModelCls = provider.get_model_cls(model.meta.model_type)
        kv = {}
        for field in ModelCls.meta.fields_display:
            kv[field] = getattr(model, field)
        return ModelCls.create_by_display(identifier=model.identifier, **kv)

    # -----
    # Songs
    # -----
    def song_upgrade(self, song: BriefSongProtocol) -> SongProtocol:
        if song.meta.flags & MF.v2:
            if MF.normal in song.meta.flags:
                upgraded_song = cast(SongProtocol, song)
            else:
                provider = self.get_or_raise(song.source)
                if self.check_flags_by_model(song, PF.get):
                    upgraded_song = provider.song_get(song.identifier)
                else:
                    raise NotSupported("provider has not flag 'get' for 'song'")
        else:
            fields = [f for f in list(SongModel.__fields__)
                      if f not in list(BaseModel.__fields__)]
            for field in fields:
                getattr(song, field)
            upgraded_song = cast(SongProtocol, song)
        return upgraded_song

    def song_list_similar(self, song: BriefSongProtocol) -> List[BriefSongProtocol]:
        provider = self.get_or_raise(song.source)
        return provider.song_list_similar(song)

    def song_list_hot_comments(self, song: BriefSongProtocol):
        provider = self.get_or_raise(song.source)
        return provider.song_list_hot_comments(song)

    def song_prepare_media(self, song: BriefSongProtocol, policy) -> Media:
        provider = self.get(song.source)
        if provider is None:
            raise MediaNotFound(f'provider:{song.source} not found')
        if song.meta.flags & MF.v2:
            # provider MUST has multi_quality flag for song
            assert self.check_flags_by_model(song, PF.multi_quality)
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
        provider = self.get(song.source)
        if provider is None:
            raise MediaNotFound(f'provider:{song.source} not found')
        song_v1 = self.cast_model_to_v1(song)
        mv = song_v1.mv
        if mv.meta.support_multi_quality:
            media, _ = mv.select_media(policy)
        else:
            media = mv.media
            if media:
                media = Media(media)
            else:
                media = None
        if not media:
            raise MediaNotFound
        return media

    def song_get_lyric(self, song: BriefSongModel):
        pass

    def song_get_mv(self, song: BriefSongModel):
        pass

    def song_get_web_url(self, song: BriefSongProtocol) -> str:
        provider = self.get_or_raise(song.source)
        return provider.song_get_web_url(song)

    # --------
    # Provider
    # --------
    def provider_has_current_user(self, source: str) -> bool:
        """Check if a provider has a logged in user

        No IO operation is triggered.

        .. versionadded:: 3.7.6
        """
        provider = self.get_or_raise(source)
        if self.check_flags(source, ModelType.none, PF.current_user):
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
        if self.check_flags(source, ModelType.none, PF.current_user):
            return provider.get_current_user()

        user_v1 = getattr(provider, '_user', None)
        if user_v1 is None:
            raise NoUserLoggedIn
        return UserModel(identifier=user_v1.identifier,
                         source=source,
                         name=user_v1.name_display,
                         avatar_url='')
