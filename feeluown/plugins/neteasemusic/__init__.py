# -*- coding: utf-8 -*-

import logging

from .nem import Nem
from .consts import LOG_FILE
from feeluown.config import config

__alias__ = '网易云音乐'
__feeluown_version__ = '1.0.4.2'
__version__ = '0.0.2'
__desc__ = '网易云音乐'

dict_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[%(levelname)s] "
                      "[%(module)s %(funcName)s %(lineno)d] "
                      ": %(message)s",
        },
    },
    'handlers': {
        'debug': {
            'formatter': 'standard',
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'release': {
            'formatter': 'standard',
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE,
            'mode': 'w',
        }
    },
    'loggers': {
        'neteasemusic': {
            'handlers': ['debug'],
            'level': logging.DEBUG,
            'propagate': True
        },
    }
}

if config.debug:
    logging.config.dictConfig(dict_config)
else:
    dict_config['loggers']['neteasemusic']['handlers'] = ['release']
    logging.config.dictConfig(dict_config)

logger = logging.getLogger(__name__)


def enable(app):
    nem = Nem(app)
    nem.ready_to_login()
    logger.info('neteasemusic plugin enabled')


def disable(app):
    logger.info('neteasemusic plugin disabled')
