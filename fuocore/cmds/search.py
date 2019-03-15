import logging
from .base import AbstractHandler
from .helpers import show_songs

logger = logging.getLogger(__name__)


class SearchHandler(AbstractHandler):
    cmds = 'search'

    def handle(self, cmd):
        return self.search_songs(cmd.args[0])

    def search_songs(self, query):
        logger.debug('搜索 %s ...', query)
        providers = self.library.list()
        source_in = [provd.identifier for provd in providers
                     if provd.Song.meta.allow_get]
        songs = []
        for result in self.library.search(query, source_in=source_in):
            logger.debug('从 %s 搜索到 %d 首歌曲，取前 20 首',
                         result.source, len(result.songs))
            songs.extend(result.songs[:20])
        logger.debug('总共搜索到 %d 首歌曲', len(songs))
        return show_songs(songs)
