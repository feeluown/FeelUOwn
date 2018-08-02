"""
feeluown.helpers
~~~~~~~~~~~~~~~~

和应用逻辑相关的一些工具函数
"""

import sys
import time
import logging
from contextlib import contextmanager
from functools import wraps


logger = logging.getLogger(__name__)


def get_model_type(model):
    return model._meta.model_type


class ActionError(Exception):
    pass


@contextmanager
def action_log(s):
    logger.info(s + '...')  # doing
    try:
        yield
    except ActionError:
        logger.warning(s + '...failed')
    except Exception:
        logger.error(s + '...error')  # failed
        raise
    else:
        logger.info(s + '...done')  # done


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
