# -*- coding:utf8 -*-

import platform
from base.logger import LOG


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


def judge_system():
    sys_info = platform.system()
    return sys_info


def judge_platform():
    platform_info = platform.platform()
    info = platform_info.split('-')
    return info