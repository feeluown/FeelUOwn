"""
feeluown.helpers
~~~~~~~~~~~~~~~~

和应用逻辑相关的一些工具函数
"""


import logging
from contextlib import contextmanager


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
