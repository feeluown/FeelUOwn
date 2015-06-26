# -*- coding:utf8 -*-

import logging

import setting


"""
log messages for developers
"""


# CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
if setting.MODE == setting.DEBUG:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s"
    )
else:
    try:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s",
            filename=setting.LOGFILE,
            filemode='w'
        )
    except:
        f = open(setting.LOGFILE, 'w')
        f.write('Create log file')
        f.close()

        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s",
            filename=setting.LOGFILE,
            filemode='w'
        )

LOG = logging.getLogger("log")

