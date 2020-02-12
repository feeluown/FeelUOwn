# -*- coding: utf-8 -*-

import logging
import logging.config

from .consts import LOG_FILE


__version__ = '3.3.10'


dict_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s %(levelname)s %(module)s] : %(message)s",
        },
        'thread': {
            'format': "[%(asctime)s %(levelname)s %(module)s %(thread)d] : %(message)s",
        },
    },
    'handlers': {},
    'loggers': {},
}


def logger_config(verbose=1, to_file=False):
    """configure logger

    :param to_file: redirect log to file
    :param verbose: verbose level.
                    0: show all (>=)warning level log
                    1: show all info level log
                    2: show feeluown/fuocore debug level log and all info log
                    3: show all debug log
    """
    handler = {'level': 'DEBUG', 'formatter': 'standard'}
    logger = {
        'handlers': [''],
        'propagate': True,
    }

    dict_config['handlers'][''] = handler
    dict_config['loggers'][''] = logger

    if to_file:
        handler.update({
            'class': 'logging.FileHandler',
            'filename': LOG_FILE,
            'mode': 'w'
        })
    else:
        handler.update({'class': 'logging.StreamHandler'})

    if verbose <= 0:
        handler['level'] = 'WARNING'
        logger['level'] = logging.WARNING
    elif verbose <= 1:
        handler['level'] = 'INFO'
        logger['level'] = logging.INFO
    else:
        handler['level'] = 'DEBUG'
        logger['level'] = logging.INFO
        if verbose >= 3:
            logger['level'] = logging.DEBUG
        else:
            # set logger for feeluown/fuocore
            fuo_logger = {
                'handlers': [''],
                'level': logging.DEBUG,
                'propagate': False,
            }
            dict_config['loggers']['feeluown'] = fuo_logger
            dict_config['loggers']['fuocore'] = fuo_logger

    logging.config.dictConfig(dict_config)
