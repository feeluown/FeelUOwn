# -*- coding:utf8 -*-

import platform
import asyncio
import json

from base.logger import LOG


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


def func_coroutine(func):
    """make the decorated function run in EventLoop

    """
    def wrapper(*args, **kwargs):
        LOG.debug("In func_coroutine: before call ")
        LOG.debug("function name is : " + func.__name__)
        APP_EVENT_LOOP = asyncio.get_event_loop()
        APP_EVENT_LOOP.call_soon(func, *args)
        LOG.debug("In func_coroutine: after call ")
    return wrapper


def write_json_into_file(data_json, filepath):
    try:
        with open(filepath, "w") as f:
            data_str = json.dumps(data_json, indent=4)
            f.write(data_str)
        return True
    except Exception as e:
        LOG.error(str(e))
        LOG.error("Write json into file failed")
        return False


def judge_system():
    sys_info = platform.system()
    return sys_info


def judge_platform():
    platform_info = platform.platform()
    info = platform_info.split('-')
    return info