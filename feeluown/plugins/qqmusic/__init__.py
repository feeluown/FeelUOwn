# -*- coding: utf-8 -*-

import logging

from fuocore.qqmusic.provider import provider
from feeluown.app import App

__alias__ = 'QQ 音乐'
__feeluown_version__ = '1.1.0'
__version__ = '0.1a0'
__desc__ = 'QQ 音乐'

logger = logging.getLogger(__name__)


def enable(app):
    app.library.register(provider)
    if app.mode & App.GuiMode:
        from feeluown.components.provider import ProviderModel

        pm = ProviderModel(
            name='QQ 音乐',
            icon='♫ ',
            desc='点击登录 QQ 音乐（未实现，欢迎 PR）\n'
                 '目前对 QQ 音乐支持比较有限：\n'
                 '- [x] 搜索音乐\n'
                 '- [ ] 查看歌手详情（欢迎 PR）\n'
                 '- [ ] 查看专辑详情（欢迎 PR）\n',
            on_click=None,
        )
        app.providers.assoc(provider.identifier, pm)


def disable(app):
    app.library.deregister(provider)
    if app.mode & App.GuiMode:
        app.providers.remove(provider.identifier)
