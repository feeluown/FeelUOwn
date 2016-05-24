# -*- coding: utf-8 -*-

import logging
import logging.config

from .consts import LOG_FILE
from .config import config


__version__ = '1.0.4.4'
__upgrade_desc__ = '''
1. 修复部分歌曲播放导致崩溃
2. 显示当前音乐加载的进度
3. 调整默认音质至 320 比特率
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
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE,
            'mode': 'w',
        }
    },
    'loggers': {
        'feeluown': {
            'handlers': ['debug'],
            'level': logging.DEBUG,
            'propagate': True
        },
    }
}


def logger_config():
    if config.debug:
        logging.config.dictConfig(dict_config)
    else:
        dict_config['loggers']['feeluown']['handlers'] = ['release']
        logging.config.dictConfig(dict_config)
