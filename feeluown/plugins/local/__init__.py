# -*- coding: utf-8 -*-

import logging
from functools import partial

from fuocore.local.provider import LocalProvider

from feeluown.app import App

__alias__ = '本地音乐'
__feeluown_version__ = '1.1.0'
__version__ = '0.1a0'
__desc__ = '本地音乐'

logger = logging.getLogger(__name__)


def enable(app):
    provider = LocalProvider()
    logger.info('Register provider: %s' % provider)
    app.library.register(provider)
    if app.mode & App.GuiMode:
        from feeluown.components.provider import ProviderModel

        pm = ProviderModel(
            name='本地音乐',
            icon='♪ ',
            desc='点击显示所有本地音乐',
            on_click=partial(app.ui.table_container.show_songs, provider.songs),
        )
        logger.info('Associate %s with %s' % (provider, pm.name))
        app.providers.assoc(provider.identifier, pm)
        app.ui.table_container.show_songs(provider.songs)


def disable(app):
    logger.info('唔，不要禁用我')
