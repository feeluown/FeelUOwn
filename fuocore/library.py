"""
音乐库模块
~~~~~~~~~~

.. code::

    from fuo_netease import provider
    library = Library()
    library.register(provider)
    library.search('周杰伦')
"""

import logging

from .utils import log_exectime

logger = logging.getLogger(__name__)


class Library(object):
    """音乐库，管理资源提供方以及资源"""
    def __init__(self):
        self._providers = set()

    def register(self, provider):
        """注册资源提供方"""
        self._providers.add(provider)

    def deregister(self, provider):
        """反注册资源提供方"""
        self._providers.remove(provider)

    def get(self, identifier):
        """通过资源提供方唯一标识获取提供方实例"""
        for provider in self._providers:
            if provider.identifier == identifier:
                return provider
        return None

    def list(self):
        """列出所有资源提供方"""
        return list(self._providers)

    def search(self, keyword, source_in=None, **kwargs):
        """search song/artist/album by keyword

        TODO: search album or artist
        """
        for provider in self._providers:
            if source_in is not None:
                if provider.identifier not in source_in:
                    continue

            try:
                result = provider.search(keyword=keyword)
            except Exception as e:
                logger.exception(str(e))
                logger.error('Search %s in %s failed.' % (keyword, provider))
            else:
                yield result

    @log_exectime
    def list_song_standby(self, song, onlyone=True):
        """try to list all valid standby

        Search a song in all providers. The typical usage scenario is when a
        song is not available in one provider, we can try to acquire it from other
        providers.

        Standby choosing strategy: search from all providers, select two song from each provide.
        Those standby song should have same title and artist name.

        TODO: maybe we should read a strategy from user config, user
        knows which provider owns copyright about an artist.

        FIXME: this method will send several network requests,
        which may block the caller.

        :param song: song model
        :param exclude: exclude providers list
        :return: list of songs (maximum count: 2)
        """
        def get_score(standby):
            score = 1
            # 分数占比关系：
            # title + album > artist
            # artist > title > album
            if song.artists_name != standby.artists_name:
                score -= 0.4
            if song.title != standby.title:
                score -= 0.3
            if song.album_name != standby.album_name:
                score -= 0.2
            return score

        valid_sources = [p.identifier for p in self.list() if p.identifier != song.source]
        q = '{} {}'.format(song.title, song.artists_name)

        standby_list = []
        for result in self.search(q, source_in=valid_sources, limit=10):
            for standby in result.songs[:2]:
                standby_list.append(standby)
        standby_list = sorted(
            standby_list,
            key=lambda standby: get_score(standby), reverse=True
        )

        valid_standby_list = []
        for standby in standby_list:
            if standby.url:
                valid_standby_list.append(standby)
                if get_score(standby) == 1 or onlyone:
                    break
                if len(valid_standby_list) >= 2:
                    break
        return valid_standby_list
