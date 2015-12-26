# -*- coding: utf-8 -*-

import asyncio
import requests
from functools import partial

from feeluown.base.logger import LOG
from feeluown.controller_api import ControllerApi
from feeluown.view_api import ViewOp


class VersionManager(object):
    current_version = 'v6.0release'

    @classmethod
    @asyncio.coroutine
    def check_release(cls):
        url = 'https://api.github.com/repos/cosven/FeelUOwn/releases'
        LOG.info('正在查找新版本...')
        try:
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(None,
                partial(requests.get, url, timeout=5))
            res = yield from future
            if not res.status_code == 200:
                LOG.warning('connect to api.github.com timeout')
                return
            releases = res.json()
            for release in releases:
                if release['tag_name'] > cls.current_version:
                    title = u'发现新版本 %s hoho' % release['tag_name']
                    LOG.info(title)
                    content = release['name']
                    ControllerApi.notify_widget.show_message(title, content)
                    ViewOp.ui.STATUS_BAR.showMessage(title, 5000)
                    break
        except Exception as e:
            LOG.error(str(e))
