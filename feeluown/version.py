import asyncio
import logging
from functools import partial


logger = logging.getLogger(__name__)


class VersionManager(object):
    current_version = 'v9.1a'

    def __init__(self, app):
        self._app = app

    @asyncio.coroutine
    def check_release(self):
        url = 'https://api.github.com/repos/cosven/FeelUOwn/releases'
        logger.info('正在查找新版本...')
        try:
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(
                None, partial(self._app.request.get, url, timeout=5))
            res = yield from future
            if not res.status_code == 200:
                logger.warning('connect to api.github.com timeout')
                return
            releases = res.json()
            for release in releases:
                if release['tag_name'] > self.current_version:
                    title = u'发现新版本 %s hoho' % release['tag_name']
                    logger.info(title)
                    self._app.message(title)
                    break
        except Exception as e:
            logger.error(str(e))
