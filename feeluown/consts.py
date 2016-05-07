# -*- coding: utf-8 -*-

import os
from enum import Enum


THEMES_DIR = './feeluown/themes/'
PLUGINS_DIR = './feeluown/plugins'
APP_ICON = './feeluown/feeluown.png'
DEFAULT_THEME_NAME = 'Solarized'


HOME_DIR = os.path.expanduser('~') + '/.FeelUOwn'

DATA_DIR = HOME_DIR + '/data'
USER_PLUGINS_DIR = HOME_DIR + '/plugins'
USER_THEMES_DIR = HOME_DIR + '/themes'
CACHE_DIR = HOME_DIR + '/cache'

LOG_FILE = HOME_DIR + '/run.log'


class PlaybackMode(Enum):
    one_loop = '单曲循环'
    sequential = '顺序'
    loop = '全部循环'
    random = '随机'
