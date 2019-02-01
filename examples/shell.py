#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from fuocore.library import Library

from fuocore.xiami import provider as xp
from fuocore.netease import provider as np
from fuocore.qqmusic import provider as lp

logging.basicConfig()
logger = logging.getLogger('fuocore')
logger.setLevel(logging.DEBUG)

lib = Library()
lib.register(xp)
lib.register(np)
lib.register(lp)

library = lib
