# -*- coding: utf-8 -*-

import logging
import logging.config

from .consts import LOG_FILE
from .config import config


__version__ = '2.0a0'
__upgrade_desc__ = '''
'''


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
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE,
            'mode': 'w',
        }
    },
    'loggers': {
        'feeluown': {
            'handlers': ['debug'],
            'level': logging.DEBUG,
            'propagate': False,
        },
        '': {
            'handlers': ['debug'],
            'level': logging.DEBUG,
            'propagate': True,
        }

    }
}


def logger_config():
    if config.debug:
        logging.config.dictConfig(dict_config)
        logging.info('Debug mode.')
    else:
        dict_config['loggers']['']['handlers'] = ['release']
        logging.config.dictConfig(dict_config)
        logging.info('Release mode.')
