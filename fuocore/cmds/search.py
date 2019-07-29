import logging
from .base import AbstractHandler
from .helpers import show_results

logger = logging.getLogger(__name__)


class SearchHandler(AbstractHandler):
    cmds = 'search'

    def handle(self, cmd):
        """
        Support command:
        - fuo search keyword
        - fuo search keyword@type=playlist
        TODO:
        - fuo search keyword[type=all]
        - fuo search keyword[type=all, format=json, source=netease, limit=10]
        :param cmd:
        :return:
        """
        options = {}
        if '@' in cmd.args[0]:
            pos = cmd.args[0].find('@')
            keyword = cmd.args[0][:pos]
            option_str = cmd.args[0][pos+1:]
            # convert "type=all, format=json," to dict
            options.update([item.split('=') for item in option_str.split(',')])
        else:
            keyword = cmd.args[0]

        if options.get('type') in ('playlists', 'playlist', 'pl'):
            stype = 1000
        else:
            stype = 1

        if len(options) >= 2 or (len(options) == 1 and 'type' not in options):
            logging.warning('have not support more options yet')

        return self.search(keyword, stype)

    def search(self, query, stype=1):
        """
        :param query:  string
        :param stype:  int  1->songs, 1000->playlists
        TODO 10->albums, 100->artists, -1->all
        :return:
        """
        logger.debug(f'搜索 {query} ...')
        providers = self.library.list()
        source_in = [provd.identifier for provd in providers
                     if provd.Song.meta.allow_get]
        results = []
        for result in self.library.search(query, stype=stype, source_in=source_in):
            if result.songs:
                logger.debug(f'从 {result.source} 搜索到 {len(result.songs)} 条歌曲，取前 20 条')
                results.extend(result.songs[:20])
            if result.playlists:
                logger.debug(f'从 {result.source} 搜索到 {len(result.playlists)} 张专辑，取前 20 条')
                results.extend(result.playlists[:20])
        logger.debug(f'总共搜索到 {len(results)} 条记录')
        return show_results(results, stype)
