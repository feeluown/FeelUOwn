# -*- coding:utf8 -*-

import logging

from feeluown.constants import MODE, DEBUG, LOGFILE


"""
log messages for developers

when to use LOG.debug() ？
    debug mode is ready for developers.
we use only LOG.info to record those errors or warning
"""


# CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
if MODE == DEBUG:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s"
    )
else:
    try:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s",
            filename=LOGFILE,
            filemode='w'
        )
    except:
        f = open(LOGFILE, 'w')
        f.write('Create log file')
        f.close()

        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] [%(filename)s line:%(lineno)d] : %(message)s",
            filename=LOGFILE,
            filemode='w'
        )

LOG = logging.getLogger("log")
