# -*- coding:utf8 -*-

from base.logger import LOG


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
            LOG.info(instances[cls])
            LOG.info(id(instances[cls]))
        return instances[cls]
    return _singleton