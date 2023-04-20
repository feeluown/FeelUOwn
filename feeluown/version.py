import asyncio
import logging
from functools import partial
from packaging import version

import requests
from requests.exceptions import ConnectionError, Timeout

from feeluown import __version__

logger = logging.getLogger(__name__)


class VersionManager(object):

    def __init__(self, app):
        self._app = app

        self._app.started.connect(self.on_app_started)

    def on_app_started(self, *args):
        loop = asyncio.get_running_loop()
        loop.call_later(
            10,
            partial(loop.create_task, self.check_release()))

    async def check_release(self):
        loop = asyncio.get_event_loop()

        logger.info('正在检测更新...')
        try:
            resp = await loop.run_in_executor(
                None,
                partial(requests.get, 'https://pypi.org/pypi/feeluown/json', timeout=2)
            )
        except (ConnectionError, Timeout) as e:
            logger.warning(e)
            logger.warning('检查更新失败')
        else:
            rv = resp.json()
            latest = version.parse(rv['info']['version'])
            current = version.parse(__version__)
            if latest > current:
                msg = '检测到新版本 %s，当前版本为 %s' % (latest, current)
                logger.warning(msg)
                if self._app.mode & self._app.GuiMode:
                    self._app.show_msg(msg)
            else:
                logger.info('当前已经是最新版本')
                if self._app.mode & self._app.GuiMode:
                    self._app.show_msg(f'当前已经是最新版本: {latest}')


if __name__ == '__main__':
    """
    测试 VersionManager 基本行为
    """

    import logging
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)

    class App(object):
        GuiMode = 0x10
        mode = 0x01

    app = App()
    mgr = VersionManager(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_task(mgr.check_release()))
