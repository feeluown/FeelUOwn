# -*- coding:utf-8 -*-

import os


"""
common settings

FUTURE:  read setting from a json file
"""

"""
path configuration
"""
ICON_PATH = '../icons'

FEELUOWN_PATH = os.path.expanduser('~') + '/.FeelUOwn'
CACHE_PATH = FEELUOWN_PATH + '/cache'
DATA_PATH = FEELUOWN_PATH + '/data'
SONGS_PATH = FEELUOWN_PATH + '/songs'

"""
mode configuration
"""
DEBUG = True   # 1 for debug
PRODUCTION = False  # 0 for Production Environment
LOGFILE = CACHE_PATH + '/error.log'
MODE = DEBUG


"""
theme configuration
"""
QSS_PATH = './themes/default.qss'


"""
web_assets configuration
"""
HTML_PATH = './web_assets/'
PUBLIC_PATH = './web_assets/public/'

"""
icon name
"""
PLAYLIST_FAVORITE = ICON_PATH + '/playlist_favorite.png'
PLAYLIST_MINE = ICON_PATH + '/Format-Bullets-01-16.png'
PLAYLIST_NORMAL = ICON_PATH + '/playlist_mine.png'
WINDOW_ICON = ICON_PATH + '/FeelUOwn.png'

"""
sqlite database name
"""
DATABASE_SQLITE = CACHE_PATH + '/data.db'

"""
config file
"""
CONFIG_FILE_PATH = FEELUOWN_PATH + '/config.yaml'
DEFAULT_CONFIG_FILE_PATH = './default_config.yaml'
