# -*- coding: utf-8 -*-

import requests

from base.logger import LOG
from controller_api import ControllerApi
from view_api import ViewOp


class VersionManager(object):
    current_version = 'v4.0a'

    @classmethod
    def check_feeluown_release(cls):
        url = 'https://api.github.com/repos/cosven/FeelUOwn/releases'
        LOG.info('正在查找新版本...')
        res = requests.get(url)
        if res.status_code == 200:
            releases = res.json()
            for release in releases:
                if release['tag_name'] > cls.current_version:
                    title = u'发现新版本 %s hoho' % release['tag_name']
                    LOG.info(title)
                    content = release['name']
                    ControllerApi.notify_widget.show_message(title, content)
                    ViewOp.ui.STATUS_BAR.showMessage(title, 5000)
                    break
