import os

from feeluown.consts import DATA_DIR


COOKIES_FILE = DATA_DIR + '/ne_cookies.json'
USER_PW_FILE = DATA_DIR + '/nem_user_pw.json'
USERS_INFO_FILE = DATA_DIR + '/nem_users_info.json'

DOWNLOAD_DIR = os.path.expanduser('~') + '/Music'