# -*- coding: utf-8 -*-

import logging
import os
import platform
import socket
import sys
import time
from collections import OrderedDict
from copy import copy, deepcopy
from functools import wraps

from fuocore.reader import Reader, RandomSequentialReader, SequentialReader


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


def reader_to_list(reader):
    if not isinstance(reader, Reader):
        raise TypeError
    if reader.allow_random_read:
        return reader.readall()
    return list(reader)


def to_reader(model, field):
    flag_attr = 'allow_create_{}_g'.format(field)
    method_attr = 'create_{}_g'.format(field)

    flag_g = getattr(model.meta, flag_attr)

    if flag_g:
        return SequentialReader.wrap(getattr(model, method_attr)())

    value = getattr(model, field, None)
    if value is None:
        return RandomSequentialReader.from_list([])
    if isinstance(value, (list, tuple)):
        return RandomSequentialReader.from_list(value)
    return SequentialReader.wrap(iter(value))  # TypeError if not iterable


class DedupList(list):
    def __init__(self, seq=(), dedup=True):
        # print("init")
        if dedup:
            dic = {} if sys.version_info[1] > 5 else OrderedDict()
            seq = list(dic.fromkeys(seq))
        self._dedup_set = set(seq)
        super().__init__(seq)

    def __getitem__(self, item):
        result = super().__getitem__(item)
        if isinstance(item, slice):
            return DedupList(result, dedup=False)
        else:
            return result

    def __add__(self, other):
        if isinstance(other, list):
            result = copy(self)
            result.extend(other)
            return result
        raise TypeError("can only concatenate list to DedupList")

    def __radd__(self, other):
        if isinstance(other, list):
            result = copy(self)
            result.extend(other)
            return result
        raise TypeError("invalid concat")

    def __setitem__(self, key, value):
        # print(f"setitem - {key} - {value}")
        self._dedup_set.remove(self[key])
        # if value not in self._dedup_set:  # this breaks item swap
        self._dedup_set.add(value)
        super().__setitem__(key, value)

    def __contains__(self, item):
        return item in self._dedup_set

    def __copy__(self):
        inter_list = list(self)
        result = self.__class__(inter_list, dedup=False)
        return result

    def __deepcopy__(self, memo):
        inter_list = [deepcopy(item) for item in self]
        result = self.__class__(inter_list, dedup=False)
        memo[id(self)] = result
        return result

    def append(self, obj):
        # print(f"append - {obj}")
        if obj not in self._dedup_set:
            self._dedup_set.add(obj)
            super().append(obj)

    def extend(self, iterable):
        # print(f"extend - {iterable}")
        for object in iterable:
            if object not in self._dedup_set:
                self._dedup_set.add(object)
                super().append(object)

    def insert(self, index: int, obj):
        # print(f"insert - {index} - {obj}")
        if obj not in self._dedup_set:
            self._dedup_set.add(obj)
            super().insert(index, obj)

    def pop(self, index: int = None):
        # print(f"pop - {index}")
        index = index if index else -1
        item = super().pop(index)
        self._dedup_set.remove(item)
        return item

    def clear(self):
        self._dedup_set.clear()
        super().clear()
