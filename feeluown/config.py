# -*- coding: utf-8 -*-

from collections.abc import MutableMapping

import yaml

from feeluown.constants import CONFIG_FILE_PATH
from feeluown.constants import DEFAULT_CONFIG_FILE_PATH
from feeluown.utils import update_dict_recursive
from feeluown.logger import LOG


# TODO: add version info to config file
class Config(MutableMapping):
    """load default config and user config

    user config can override default config
    """
    def __init__(self):
        self._data = dict()

    # TODO: bugy update policy
    def load(self, path=CONFIG_FILE_PATH):
        # load default config first, there may be some new key field which not
        # exists in user config
        with open(DEFAULT_CONFIG_FILE_PATH, 'r') as f:
            self._data.update(yaml.load(f))
        try:
            with open(path, 'r') as f:
                update_dict_recursive(self._data, yaml.load(f))
        except OSError:
            LOG.error('user config file not found, will load default config')

    def save(self, path=CONFIG_FILE_PATH):
        with open(path, 'w') as f:
            f.write(yaml.dump(self._data))
            LOG.info('save user config.')

    def __getitem__(self, key):
        return self._data[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self._data[self.__keytransform__(key)] = value

    def __keytransform__(self, key):
        return key

    def __delitem__(self, key):
        del self._data[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return iter(self._data)

    def on_playback_mode_change(self, mode):
        self._data['player']['playback_mode'] = mode


config = Config()
