# -*- coding: utf-8 -*-

import logging

from .consts import LOG_FILE
from .config import config


def logger_config():
    if config.debug:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s",
        )
    else:
        logging.basicConfig(
            format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s",
            level=logging.INFO,
            filename=LOG_FILE,
            filemode='w',
        )
