# -*- coding: utf-8 -*-

import os
import importlib
import logging

from fuocore.dispatch import Signal
from .consts import USER_PLUGINS_DIR, PLUGINS_DIR

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Plugin(object):
    def __init__(self, module, alias='', version='', desc='',
                 author='', homepage=''):
        """插件对象

        :param name: 插件名
        :param version: 插件版本
        :param module: 插件模块对象，它有 enable 和 disable 方法
        :param desc: 插件描述
        """
        self.alias = alias
        self.name = module.__name__
        self._module = module
        self.version = version
        self.desc = desc
        self.author = author
        self.homepage = homepage
        self.is_enabled = False

    def enable(self, app):
        self._module.enable(app)
        self.is_enabled = True

    def disable(self, app):
        self._module.disable(app)
        self.is_enabled = False


class PluginsManager:
    """在 App 初始化完成之后，加载插件

    TODO: 以后可能需要支持在 App 初始化完成之前加载插件
    """

    scan_finished = Signal()

    def __init__(self, app):
        super().__init__()
        self._app = app

        self._plugins = {}

    def load(self, plugin):
        plugin.enable(self._app)

    def unload(self, plugin):
        plugin.disable(self._app)

    def scan(self):
        logger.debug('Scaning plugins...')
        modules_name = [p for p in os.listdir(PLUGINS_DIR)
                        if os.path.isdir(os.path.join(PLUGINS_DIR, p))]
        modules_name.extend([p for p in os.listdir(USER_PLUGINS_DIR)
                            if os.path.isdir(os.path.join(USER_PLUGINS_DIR))])
        for module_name in modules_name:
            try:
                module = importlib.import_module(module_name)
                plugin_alias = module.__alias__
                plugin = Plugin(module, alias=plugin_alias)
                plugin.enable(self._app)
                logger.info('detect plugin: %s.' % plugin_alias)
            except:  # noqa
                logger.exception('detect a bad plugin %s' % module_name)
            else:
                self._plugins[plugin.name] = plugin
        logger.debug('Scaning plugins...done')

        self.scan_finished.emit(list(self._plugins.values()))
