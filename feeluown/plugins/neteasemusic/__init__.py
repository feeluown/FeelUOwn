# -*- coding: utf-8 -*-

import logging

from .nem import Nem

__alias__ = '网易云音乐'
__version__ = '0.0.1'
__desc__ = '网易云音乐'


def enable(app):
    logger = logging.getLogger(__name__)
    Nem(app)
    logger.info('neteasemusic plugin enabled')


def disable(app):
    logger = logging.getLogger(__name__)
    logger.info('neteasemusic plugin disabled')
