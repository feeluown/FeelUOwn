# -*- coding: utf-8 -*-

import logging
from functools import partial

from fuocore.qqmusic.provider import provider
from fuocore.qqmusic.models import search
from feeluown.components.library import LibraryModel
import fuocore.qqmusic.models  # noqa

__alias__ = 'QQ 音乐'
__feeluown_version__ = '1.1.0'
__version__ = '0.1a0'
__desc__ = 'QQ 音乐'

logger = logging.getLogger(__name__)


def enable(app):
    library = LibraryModel(
        provider=provider,
        icon='♫ ',
        on_click=None,
        search=search,
        desc='点击登录 QQ 音乐（未实现，欢迎 PR）',
    )
    app.libraries.register(library)


def disable(app):
    pass
