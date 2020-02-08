# -*- coding: utf-8 -*-

import logging
import os
import platform
import socket
import time
from functools import wraps
from string import Formatter

from fuocore.reader import Reader, RandomSequentialReader, SequentialReader


logger = logging.getLogger(__name__)

widths = [
    (126, 1), (159, 0), (687, 1), (710, 0), (711, 1),
    (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
    (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1),
    (8426, 0), (9000, 1), (9002, 2), (11021, 1), (12350, 2),
    (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1),
    (55203, 2), (63743, 1), (64106, 2), (65039, 1), (65059, 0),
    (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
    (120831, 1), (262141, 2), (1114109, 1),
]


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


def char_len(c):
    if ord(c) == 0xe or ord(c) == 0xf:
        return 0
    for num, wid in widths:
        if ord(c) <= num:
            return wid
    return 1


def _fit_text(text, length, filling=True):
    """裁剪或者填补字符串，控制其显示的长度

    >>> _fit_text('12345', 6)
    '12345 '
    >>> _fit_text('哈哈哈哈哈s', 6)  # doctest: -ELLIPSIS
    '哈哈 …'
    >>> _fit_text('哈s哈哈哈哈s', 6)  # doctest: -ELLIPSIS
    '哈s哈…'
    >>> _fit_text('sssss', 5)
    'sssss'

    FIXME: 这样可能会截断一些英文词汇
    """
    assert 80 >= length >= 5

    text_len = 0
    len_index_map = {}
    for i, c in enumerate(text):
        text_len += char_len(c)
        len_index_map[text_len] = i

    if text_len <= length:
        if filling:
            return text + (length - text_len) * ' '
        return text

    remain = length - 1
    if remain in len_index_map:
        return text[:(len_index_map[remain] + 1)] + '…'
    else:
        return text[:(len_index_map[remain - 1] + 1)] + ' …'


class WideFormatter(Formatter):
    """
    Custom string formatter that handles new format parameters:
    '_': _fit_text(*, filling=False)
    '+': _fit_text(*, filling=True)
    """
    def format_field(self, value, format_spec):
        fmt_type = format_spec[0] if format_spec else None
        if fmt_type == "_":
            return _fit_text(value, int(format_spec[1:]), filling=False)
        if fmt_type == "+":
            return _fit_text(value, int(format_spec[1:]), filling=True)
        return format(value, format_spec)