# -*- coding: utf-8 -*-

from feeluown.logger import LOG
from feeluown.controller_api import ControllerApi
from feeluown.view_api import ViewOp

from .normalize import NetEaseAPI
from .model import UserDb

netease_normalize = NetEaseAPI()


def init(controller):

    LOG.info("NetEase Plugin init")

    ControllerApi.api = netease_normalize

    user = UserDb.get_last_login_user()
    if user is not None:
        netease_normalize.set_uid(user.uid)
        user_data = user.basic_info
        if user.cookies is not None:
            netease_normalize.ne.load_cookies(user.cookies)
            if netease_normalize.login_by_cookies():
                ControllerApi.set_login()
                ViewOp.load_user_infos(user_data)
