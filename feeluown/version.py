import asyncio
import logging
from functools import partial


logger = logging.getLogger(__name__)


class VersionManager(object):
    current_version = 'v9.5a'

    def __init__(self, app):
        self._app = app

    @asyncio.coroutine
    def check_release(self):
        pass
