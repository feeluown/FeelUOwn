# -*- coding: utf-8 -*-

import os
import importlib
import logging

from .consts import USER_PLUGINS_DIR, PLUGINS_DIR


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PluginsManager(object):
    def __init__(self, app):
        super().__init__()
        self._app = app

        self._plugins = {}

    def load(self, plugin):
        plugin.enable(self._app)

    def unload(self, plugin):
        plugin.disable(self._app)

    def scan(self):
        modules_name = [p for p in os.listdir(PLUGINS_DIR)
                        if os.path.isdir(os.path.join(PLUGINS_DIR, p))]
        modules_name.extend([p for p in os.listdir(USER_PLUGINS_DIR)
                             if os.path.isdir(os.path.join(USER_PLUGINS_DIR))])
        for module_name in modules_name:
            try:
                module = importlib.import_module(module_name)
                plugin_name = module.__alias__
                self._plugins[plugin_name] = module
                module.enable(self._app)
                logger.info('detect plugin: %s.' % plugin_name)
            except:
                logger.exception('detect a bad plugin %s' % module_name)
