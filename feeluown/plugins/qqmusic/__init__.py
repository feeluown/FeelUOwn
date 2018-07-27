# -*- coding: utf-8 -*-

import logging

from fuocore.qqmusic.provider import provider
from feeluown.app import App
from feeluown.components.provider import ProviderModel
import fuocore.qqmusic.models  # noqa

__alias__ = 'QQ 音乐'
__feeluown_version__ = '1.1.0'
__version__ = '0.1a0'
__desc__ = 'QQ 音乐'

logger = logging.getLogger(__name__)


def enable(app):
    app.library.register(provider)
    if app.mode & App.GUIMode:
        pm = ProviderModel(
            name='QQ 音乐',
            icon='♫ ',
            desc='点击登录 QQ 音乐（未实现，欢迎 PR）',
            on_click=None,
        )
        app.providers.assoc(provider.identifier, pm)


def disable(app):
    app.providers.remove(provider.identifier)
    app.library.deregister(provider)
