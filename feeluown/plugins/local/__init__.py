# -*- coding: utf-8 -*-

import logging
from functools import partial

from fuocore.local.provider import LocalProvider
from feeluown.components.library import LibraryModel

__alias__ = '本地音乐'
__feeluown_version__ = '1.1.0'
__version__ = '0.1a0'
__desc__ = '本地音乐'

logger = logging.getLogger(__name__)


def enable(app):
    provider = LocalProvider()
    library = LibraryModel(
        provider=provider,
        icon='♪ ',
        on_click=partial(app.ui.table_container.show_songs, provider.songs),
        search=None,
        desc='点击显示所有本地音乐'
    )
    app.libraries.register(library)
    app.ui.table_container.show_songs(provider.songs)


def disable(app):
    pass
