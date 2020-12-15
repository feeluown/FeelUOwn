import logging
from .base import AbstractHandler

logger = logging.getLogger(__name__)


class SearchHandler(AbstractHandler):
    """

    Supported query parameters:

    search keyword
    search keyword [type=playlist]

    TODO:

    search keyword [type=all,source=netease,limit=10]
    """

    cmds = 'search'

    def handle(self, cmd):
        return self.search(cmd.args[0], cmd.options)

    def search(self, keyword, options=None):
        """

        :param string keyword: serach keyword
        :param dict options: search options
        :return:
        """
        providers = self.library.list()
        source_in = [provd.identifier for provd in providers
                     if provd.Song.meta.allow_get]
        params = {'source_in': source_in}
        if options is not None:
            type_in = options.pop('type', None)
            source_in = options.pop('source', None)
            if type_in is not None:
                params['type_in'] = type_in
            if source_in is not None:
                params['source_in'] = source_in.split(',')
            if options:
                logger.warning('Unknown cmd options: %s', options)
        # TODO: limit output lines
        return list(self.library.search(keyword, **params))
