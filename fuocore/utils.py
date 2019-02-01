# -*- coding: utf-8 -*-

from functools import wraps
import logging
import time


logger = logging.getLogger(__name__)


def log_exectime(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t = time.process_time()
        result = func(*args, **kwargs)
        elapsed_time = time.process_time() - t
        logger.debug('function %s executed time: %f ms',
                     func.__name__, elapsed_time * 1000)
        return result
    return wrapper


def elfhash(s):
    """
    :param string: bytes

    >>> import base64
    >>> s = base64.b64encode(b'hello world')
    >>> elfhash(s)
    224648685
    """
    hash = 0
    x = 0
    for c in s:
        hash = (hash << 4) + c
        x = hash & 0xF0000000
        if x:
            hash ^= (x >> 24)
            hash &= ~x
    return (hash & 0x7FFFFFFF)


def find_previous(element, l):
    """
    find previous element in a sorted list

    >>> find_previous(0, [0])
    0
    >>> find_previous(2, [1, 1, 3])
    1
    >>> find_previous(0, [1, 2])
    >>> find_previous(1.5, [1, 2])
    1
    >>> find_previous(3, [1, 2])
    2
    """
    length = len(l)
    for index, current in enumerate(l):
        # current is the last element
        if length - 1 == index:
            return current

        # current is the first element
        if index == 0:
            if element < current:
                return None

        if current <= element < l[index+1]:
            return current
