# -*- coding: utf-8 -*-

import logging

from .nem import Nem
from .consts import LOG_FILE
from feeluown.config import config

__alias__ = '网易云音乐'
__feeluown_version__ = '1.0.4.2'
__version__ = '0.0.2'
__desc__ = '网易云音乐'

logger = logging.getLogger(__name__)


def enable(app):
    nem = Nem(app)
    nem.initialize()
    logger.info('neteasemusic plugin enabled')


def disable(app):
    logger.info('neteasemusic plugin disabled')
