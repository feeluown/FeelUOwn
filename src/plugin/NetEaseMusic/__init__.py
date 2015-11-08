# -*- coding: utf-8 -*-

import os
import json

from base.logger import LOG
from base.utils import func_coroutine
from constants import DATA_PATH
from controller_api import ControllerApi
from view_api import ViewOp

from .normalize import NetEaseAPI

netease_normalize = NetEaseAPI()


def init(controller):
    """init plugin """

    LOG.info("NetEase Plugin init")

    ControllerApi.api = netease_normalize

    if os.path.exists(DATA_PATH + netease_normalize.user_info_filename):
        with open(DATA_PATH + netease_normalize.user_info_filename) as f:
            data = f.read()
            data_dict = json.loads(data)
            if "uid" in data_dict:
                netease_normalize.uid = data_dict['uid']
                ViewOp.load_user_infos(data_dict)

    if os.path.exists(DATA_PATH + netease_normalize.ne.cookies_filename):
        @func_coroutine
        def check_cookies():
            netease_normalize.ne.load_cookies()
            if netease_normalize.check_login_successful():
                ControllerApi.set_login()
        check_cookies()
    else:
        LOG.info("找不到您的cookies文件，请您手动登录")
