# -*- coding: utf-8 -*-

import logging
import logging.config

from .consts import LOG_FILE


__version__ = '3.0a5'


dict_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[%(levelname)s] "
                      "[%(filename)s %(funcName)s %(lineno)d] "
                      ": %(message)s",
        },
    },
    'handlers': {
        'debug': {
            'formatter': 'standard',
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'cli-release': {
            'formatter': 'standard',
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'gui-release': {
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
        'fuocore': {
            'handlers': ['debug'],
            'level': logging.DEBUG,
            'propagate': False,
        },
        # 其它模块使用这个 logger
        '': {
            'handlers': ['debug'],
            'level': logging.DEBUG,
            'propagate': True,
        }

    }
}


def logger_config(debug, to_file=False):
    if debug:
        logging.config.dictConfig(dict_config)
        logging.info('Debug mode.')
    else:
        if to_file:
            dict_config['loggers']['']['handlers'] = ['gui-release']
            dict_config['loggers']['feeluown']['handlers'] = ['gui-release']
            dict_config['loggers']['fuocore']['handlers'] = ['gui-release']
        else:
            dict_config['loggers']['']['handlers'] = ['cli-release']
            dict_config['loggers']['feeluown']['handlers'] = ['cli-release']
            dict_config['loggers']['fuocore']['handlers'] = ['cli-release']

        logging.config.dictConfig(dict_config)
        logging.info('Release mode.')
