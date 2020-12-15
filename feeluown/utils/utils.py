# -*- coding: utf-8 -*-

import logging
import os
import sys
import time
from collections import OrderedDict
from copy import copy, deepcopy
from functools import wraps
from itertools import filterfalse

from feeluown.utils.reader import wrap as reader_wrap


logger = logging.getLogger(__name__)


def use_mpv_old():
    try:
        import mpv  # noqa
    except AttributeError as e:
        # undefined symbol: mpv_render_context_create
        msg = str(e)
        if 'undefined symbol' in msg:
            logger.info(f'use mpv old because of err: {msg}')
            return True
    return False


def parse_ms(ms):
    minute = int(ms / 60000)
    second = int((ms % 60000) / 1000)
    return minute, second


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


def find_previous(element, list_):
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
    length = len(list_)
    for index, current in enumerate(list_):
        # current is the last element
        if length - 1 == index:
            return current

        # current is the first element
        if index == 0:
            if element < current:
                return None

        if current <= element < list_[index+1]:
            return current


def get_osx_theme():
    """1 for dark, -1 for light"""
    with os.popen('defaults read -g AppleInterfaceStyle') as pipe:
        theme = pipe.read().strip()
    return 1 if theme == 'Dark' else -1


def to_reader(model, field):
    flag_attr = 'allow_create_{}_g'.format(field)
    method_attr = 'create_{}_g'.format(field)

    flag_g = getattr(model.meta, flag_attr)

    if flag_g:
        return reader_wrap(getattr(model, method_attr)())

    value = getattr(model, field, None)
    if value is None:
        return reader_wrap([])
    if isinstance(value, (list, tuple)):
        return reader_wrap(value)
    return reader_wrap(iter(value))  # TypeError if not iterable


def to_readall_reader(*args, **kwargs):
    """
    hack: set SequentialReader reader's count to 1000 if it is None
    so that we can call readall method.
    """
    reader = to_reader(*args, **kwargs)
    if reader.count is None:
        reader.count = 1000
    return reader


class DedupList(list):
    """ List that doesn't contain duplicate items """

    def _get_index(self, index):
        """ project idx into range(len) """
        if index <= -len(self):
            return 0
        if index < 0:
            return index + len(self)
        if index >= len(self):
            return len(self)
        return index

    @staticmethod
    def dic():
        """ return a dict that remembers insertion order """
        return {} if sys.version_info[1] > 5 else OrderedDict()

    def __init__(self, seq=(), dedup=True):
        if dedup:
            seq = self.dic().fromkeys(seq)
        # keep idx in a dict for dedup and index
        self._map = dict(zip(seq, range(len(seq))))
        super().__init__(seq)

    def __getitem__(self, item):
        result = super().__getitem__(item)
        if isinstance(item, slice):
            # Always return a DedupList when slicing to avoid accidentally
            # convert a DedupList to normal list.
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
            if isinstance(other, DedupList):
                result = copy(other)
            else:
                # To avoid accidentally convert a DedupList to normal list.
                result = DedupList(other)
            result.extend(self)
            return result
        raise TypeError("invalid concat")

    def __setitem__(self, key, value):
        if value in self._map:
            raise ValueError("item already exists in DedupList")
        self._map.pop(self[key])
        self._map[value] = key
        super().__setitem__(key, value)

    def __contains__(self, item):
        return item in self._map

    def __copy__(self):
        result = DedupList(self, dedup=False)
        return result

    def __deepcopy__(self, memo):
        inter_list = [deepcopy(item) for item in self]
        result = DedupList(inter_list, dedup=False)
        memo[id(self)] = result
        return result

    def swap(self, idx_1, idx_2):
        item_1 = self[idx_1]
        item_2 = self[idx_2]
        self._map[item_1] = idx_2
        self._map[item_2] = idx_1
        super().__setitem__(idx_1, item_2)
        super().__setitem__(idx_2, item_1)

    def sort(self, *args, **kwargs):
        super().sort(*args, **kwargs)
        self._map = dict(zip(self, range(len(self))))

    def append(self, obj):
        if obj not in self._map:
            self._map[obj] = len(self)
            super().append(obj)

    def extend(self, iterable):
        length = len(self)
        append_list = list(filterfalse(self._map.__contains__, iterable))   # dedup
        self._map.update(zip(append_list, range(length, length + len(append_list))))
        super().extend(append_list)

    def index(self, object, start: int = None, stop: int = None):
        if object not in self._map:
            raise ValueError("not in list")
        # get idx from _map directly
        idx = self._map[object]
        if start:
            if not stop:
                stop = len(self)
            if idx not in range(start, stop):
                raise ValueError("not in list")
        return idx

    def insert(self, index: int, obj):
        if obj not in self._map:
            # insert accepts out-of-range indices, but we don't want them in our _map
            index = self._get_index(index)
            # all idx in _map after 'index' should be changed
            for key, idx in self._map.items():
                if idx >= index:
                    self._map[key] = idx + 1
            self._map[obj] = index
            super().insert(index, obj)

    def pop(self, index: int = None):
        index = index if index is not None else -1
        item = super().pop(index)
        # list.pop() returns an index, so no need to calculate manually like 'insert'
        index = self._map.pop(item)
        # all idx in _map after 'index' should be changed
        for obj, idx in self._map.items():
            if idx > index:
                self._map[obj] = idx - 1
        return item

    def remove(self, item):
        if item not in self._map:
            # raise same exception as list
            raise ValueError("list.remove(x): x not in list")
        idx = self._map[item]
        self.pop(idx)

    def clear(self):
        self._map.clear()
        super().clear()
