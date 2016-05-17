# -*- coding: utf-8 -*-

import logging

from .consts import LOG_FILE
from .config import config


__version__ = '1.0.3'


def logger_config():
    if config.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s",
        )
    else:
        logging.basicConfig(
            format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s",
            level=logging.DEBUG,
            filename=LOG_FILE,
            filemode='w',
        )
