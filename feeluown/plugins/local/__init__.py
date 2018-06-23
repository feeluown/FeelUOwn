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
    app.provider_manager.register(provider)

    library = LibraryModel(
        identifier='local',
        name='本地音乐',
        icon='♪  ',
        load_cb=partial(app.ui.songs_table_container.show_songs, provider.songs)
    )
    app.libraries.add_library(library)
    app.ui.songs_table_container.show_songs(provider.songs)


def disable(app):
    pass
