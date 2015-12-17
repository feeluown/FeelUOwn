# -*- coding:utf-8 -*-

import random

from controller_api import ControllerApi
from tips import tips


class TipsManager(object):

    @staticmethod
    def show_start_tip():
        tips_content = list(tips.values())
        index = random.randint(0, len(tips_content)-1)
        ControllerApi.notify_widget.show_message("Tips", tips_content[index])
