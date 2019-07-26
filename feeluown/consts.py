# -*- coding: utf-8 -*-

import os

APP_ICON = './feeluown/feeluown.png'

HOME_DIR = os.path.expanduser('~') + '/.FeelUOwn'

DATA_DIR = HOME_DIR + '/data'
USER_PLUGINS_DIR = HOME_DIR + '/plugins'
USER_THEMES_DIR = HOME_DIR + '/themes'
CACHE_DIR = HOME_DIR + '/cache'
SONG_DIR = HOME_DIR + '/songs'
COLLECTIONS_DIR = HOME_DIR + '/collections'

LOG_FILE = HOME_DIR + '/stdout.log'
DEFAULT_RCFILE_PATH = os.path.expanduser('~/.fuorc')
