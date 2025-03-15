# -*- coding: utf-8 -*-

import os

# USER_HOME variable is design for mobile application (feeluownx)
USER_HOME = os.environ.get('FEELUOWN_USER_HOME', os.path.expanduser('~'))
HOME_DIR = os.path.expanduser(USER_HOME + '/.FeelUOwn')

DATA_DIR = HOME_DIR + '/data'
USER_PLUGINS_DIR = HOME_DIR + '/plugins'
USER_THEMES_DIR = HOME_DIR + '/themes'
CACHE_DIR = HOME_DIR + '/cache'
SONG_DIR = HOME_DIR + '/songs'
COLLECTIONS_DIR = HOME_DIR + '/collections'

LOG_FILE = HOME_DIR + '/stdout.log'
STATE_FILE = os.path.join(DATA_DIR, 'state.json')
DEFAULT_RCFILE_PATH = os.path.expanduser(f'{USER_HOME}/.fuorc')
