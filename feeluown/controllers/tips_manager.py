# -*- coding:utf-8 -*-

import random

from feeluown.controller_api import ControllerApi
from feeluown.tips import tips


class TipsManager(object):

    @staticmethod
    def show_start_tip():
        tips_content = list(tips.values())
        index = random.randint(0, len(tips_content)-1)
        ControllerApi.notify_widget.show_message("Tips", tips_content[index])
