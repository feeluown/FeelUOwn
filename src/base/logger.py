# -*- coding:utf8 -*-

import logging

import constants


"""
log messages for developers
"""


# CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
if constants.MODE == constants.DEBUG:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s"
    )
else:
    try:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s",
            filename=constants.LOGFILE,
            filemode='w'
        )
    except:
        f = open(constants.LOGFILE, 'w')
        f.write('Create log file')
        f.close()

        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s",
            filename=constants.LOGFILE,
            filemode='w'
        )

LOG = logging.getLogger("log")

