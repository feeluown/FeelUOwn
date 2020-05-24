import logging
from functools import partial

from fuocore import aio
from fuocore.dispatch import Signal
from fuocore.models import SearchType
from fuocore.provider import AbstractProvider
from fuocore.utils import log_exectime

logger = logging.getLogger(__name__)


class ProviderAlreadyExists(Exception):
    pass


class ProviderNotFound(Exception):
    pass


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

        >>> from fuocore.provider import dummy_provider
        >>> library = Library(None)
        >>> library.register(dummy_provider)
        >>> library.register(dummy_provider)
        Traceback (most recent call last):
            ...
        fuocore.library.ProviderAlreadyExists
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

        results = []
        # TODO: use async generator when we only support Python 3.6 or above
        for future in aio.as_completed(fs, timeout=timeout):
            try:
                result = await future
            except Exception as e:
                logger.exception(str(e))
            else:
                if result is not None:
                    results.append(result)
        return results

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

    async def a_list_song_standby(self, song, onlyone=True):
        """async version of list_song_standby
        """
        providers = self._providers_standby or [pvd.identifier for pvd in self.list()]
        valid_providers = [provider for provider in providers
                           if provider != song.source]
        q = '{} {}'.format(song.title_display, song.artists_name_display)
        result_g = await self.a_search(q, source_in=valid_providers)
        sorted_standby_list = _extract_and_sort_song_standby_list(song, result_g)
        # choose one or two valid standby
        result = []
        for standby in sorted_standby_list:
            url = await aio.run_in_executor(None, lambda: standby.url)
            if url:
                result.append(standby)
                if onlyone or len(result) >= 2:
                    break
        return result
