# -*- coding: utf-8 -*-

import os
import sys
# USER_HOME variable is design for mobile application (feeluownx)
USER_HOME = os.environ.get('FEELUOWN_USER_HOME', os.path.expanduser('~'))

_old_home_dir = os.path.join(USER_HOME, '.FeelUOwn')

if sys.platform == 'linux' and not os.path.exists(_old_home_dir):
    CONFIG_DIR = os.environ.get(
        'XDG_CONFIG_HOME', os.path.join(USER_HOME, '.config'))
    DATA_DIR = os.environ.get(
        'XDG_DATA_HOME', os.path.join(USER_HOME, '.local', 'share'))
    STATE_DIR = os.environ.get(
        'XDG_STATE_HOME', os.path.join(USER_HOME, '.local', 'state'))
    CACHE_DIR = os.environ.get(
        'XDG_CACHE_HOME', os.path.join(USER_HOME, '.cache'))

    HOME_DIR = os.path.join(CONFIG_DIR, 'feeluown')
    DATA_DIR = os.path.join(DATA_DIR, 'feeluown')
    STATE_DIR = os.path.join(STATE_DIR, 'feeluown')
    CACHE_DIR = os.path.join(CACHE_DIR, 'feeluown')

    USER_PLUGINS_DIR = os.path.join(DATA_DIR, 'plugins')
    USER_THEMES_DIR = os.path.join(DATA_DIR, 'themes')
    SONG_DIR = os.path.join(DATA_DIR, 'songs')
    COLLECTIONS_DIR = os.path.join(DATA_DIR, 'collections')

    LOG_FILE = os.path.join(STATE_DIR, 'stdout.log')
    STATE_FILE = os.path.join(STATE_DIR, 'state.json')
    DEFAULT_RCFILE_PATH = os.path.join(HOME_DIR, 'fuorc')
else:
    HOME_DIR = _old_home_dir
    DATA_DIR = os.path.join(HOME_DIR, 'data')
    USER_PLUGINS_DIR = os.path.join(HOME_DIR, 'plugins')
    USER_THEMES_DIR = os.path.join(HOME_DIR, 'themes')
    CACHE_DIR = os.path.join(HOME_DIR, 'cache')
    SONG_DIR = os.path.join(HOME_DIR, 'songs')
    COLLECTIONS_DIR = os.path.join(HOME_DIR, 'collections')

    LOG_FILE = os.path.join(HOME_DIR, 'stdout.log')
    STATE_FILE = os.path.join(DATA_DIR, 'state.json')
    DEFAULT_RCFILE_PATH = os.path.join(USER_HOME, '.fuorc')
