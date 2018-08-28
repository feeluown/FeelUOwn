# -*- coding: utf-8 -*-

import logging

from fuocore.xiami.provider import provider
from feeluown.app import App

__alias__ = '虾米音乐'
__feeluown_version__ = '1.1.0'
__version__ = '0.1a0'
__desc__ = '虾米音乐'

logger = logging.getLogger(__name__)


def enable(app):
    app.library.register(provider)


def disable(app):
    app.library.deregister(provider)
