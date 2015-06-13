# -*- coding:utf8 -*-

"""
common settings

FUTURE:  read setting from a json file
"""


"""
path configuration
"""
ICON_PATH = '../icons/'
CACHE_PATH = '../cache/'
DATA_PATH = '../DATA/'


"""
mode configuration
"""
DEBUG = True   # 1 for debug
PRODUCTION = False  # 0 for Production Environment
MODE = DEBUG


"""
theme configuration
"""
QSS_PATH = 'themes/default.qss'


"""
web_assets configuration
"""
HTML_PATH = 'web_assets/'
PUBLIC_PATH = 'web_assets/public/'

"""
icon name
"""
PLAYLIST_FAVORITE = ICON_PATH + 'playlist_favorite.png'
PLAYLIST_MINE = ICON_PATH + 'Format-Bullets-01-16.png'
PLAYLIST_NORMAL = ICON_PATH + 'playlist_mine.png'