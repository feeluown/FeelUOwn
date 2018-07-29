# -*- coding: utf-8 -*-

import logging

from fuocore.netease.provider import provider
from feeluown.app import App
from feeluown.components.provider import ProviderModel

from .nem import Nem
from .consts import LOG_FILE


__alias__ = '网易云音乐'
__feeluown_version__ = '1.0.4.2'
__version__ = '0.0.2'
__desc__ = '网易云音乐'

logger = logging.getLogger(__name__)


def enable(app):
    app.library.register(provider)

    if app.mode & App.GuiMode:
        nem = Nem(app)
        pm = ProviderModel(
            name='网易云音乐',
            desc='点击可以登录',
            on_click=nem.ready_to_login,
        )
        nem._pm = pm
        app.providers.assoc(provider.identifier, pm)


def disable(app):
    app.provider.remove(provider.identifier)
    app.library.deregister(provider)
