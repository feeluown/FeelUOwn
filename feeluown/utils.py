# -*- coding:utf-8 -*-

import collections
import platform
import json
import time
from functools import wraps

from .logger import LOG


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


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


def show_requests_progress(response, signal=None):
    content = bytes()
    total_size = response.headers.get('content-length')
    if total_size is None:
        content = response.content
        return content
    else:
        total_size = int(total_size)
        bytes_so_far = 0

        for chunk in response.iter_content(102400):
            content += chunk
            bytes_so_far += len(chunk)
            progress = round(bytes_so_far * 1.0 / total_size * 100)
            if signal is not None:
                signal.emit(progress)
        return content


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t = time.process_time()
        result = func(*args, **kwargs)
        elapsed_time = time.process_time() - t
        LOG.info('function %s executed time: %f s'
                 % (func.__name__, elapsed_time))
        return result
    return wrapper


def is_mac():
    if platform.system() == 'Darwin':
        return True
    return False


def is_linux():
    if platform.system() == 'Linux':
        return True
    return False


def update_dict_recursive(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            r = update_dict_recursive(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d
