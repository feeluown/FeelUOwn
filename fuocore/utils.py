# -*- coding: utf-8 -*-

import logging
import os
import platform
import socket
import time
from functools import wraps


logger = logging.getLogger(__name__)


def parse_ms(ms):
    minute = int(ms / 60000)
    second = int((ms % 60000) / 1000)
    return minute, second


def is_linux():
    if platform.system() == 'Linux':
        return True
    return False


def is_osx():
    if platform.system() == 'Darwin':
        return True
    return False


def is_port_used(port, host='0.0.0.0'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rv = sock.connect_ex((host, port))
    return rv == 0


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


def get_osx_theme():
    """1 for dark, -1 for light"""
    with os.popen('defaults read -g AppleInterfaceStyle') as pipe:
        theme = pipe.read().strip()
    return 1 if theme == 'Dark' else -1
