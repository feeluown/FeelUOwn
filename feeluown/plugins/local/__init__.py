# -*- coding: utf-8 -*-

import asyncio
import logging
from functools import partial

from fuocore.local import provider

from feeluown.app import App

__alias__ = '本地音乐'
__feeluown_version__ = '1.1.0'
__version__ = '0.1a0'
__desc__ = '本地音乐'

logger = logging.getLogger(__name__)


def show_provider(app):
    app.playlists.clear()
    # app.playlists.add(provider.playlists)

    app.ui.left_panel.my_music_con.hide()
    app.ui.left_panel.playlists_con.hide()
    app.ui.table_container.show_songs(provider.songs)


def enable(app):
    logger.info('Register provider: %s', provider)
    loop = asyncio.get_event_loop()
    future_scan = loop.run_in_executor(None, provider.scan)
    app.library.register(provider)
    if app.mode & App.GuiMode:
        from feeluown.components.provider import ProviderModel

        pm = ProviderModel(
            name='本地音乐',
            icon='♪ ',
            desc='点击显示所有本地音乐',
            on_click=partial(show_provider, app),
        )
        logger.info('Associate %s with %s', provider, pm.name)
        app.providers.assoc(provider.identifier, pm)
        future_scan.add_done_callback(lambda _: show_provider(app))


def disable(app):
    logger.info('唔，不要禁用我')
