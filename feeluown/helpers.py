"""
feeluown.helpers
~~~~~~~~~~~~~~~~

和应用逻辑相关的一些工具函数
"""
import asyncio
import sys
import time
import logging
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)


def get_model_type(model):
    return model._meta.model_type


async def async_run(func, loop=None, executor=None):
    """异步的获取 model 属性值

    值得注意的是，如果 executor 消费队列排队了，这个会卡住。
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func)


class ActionError(Exception):
    pass


def use_mac_theme():
    """判断是否需要使用 mac 主题

    目前只是简单为 mac 做一些定制，但如果真的要引入 theme 这个概念，
    单这一个函数是不够的。
    """
    return True
    return sys.platform == 'darwin'


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t = time.process_time()
        result = func(*args, **kwargs)
        elapsed_time = time.process_time() - t
        logger.info('function %s executed time: %f s'
                    % (func.__name__, elapsed_time))
        return result
    return wrapper
