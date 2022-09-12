# -*- coding: utf-8 -*-

import importlib
import logging
import os
import sys

from feeluown.config import Config
from feeluown.utils.dispatch import Signal
from .consts import USER_PLUGINS_DIR

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class InvalidPluginError(Exception):
    pass


class Plugin:
    """
    A plugin can be a Python module or package which implements
    `enable(app)` and `disable(app)` function. It can also implements
    `init_config(config)` and initialize its configurations.
    """
    def __init__(self, module, alias='', version='', desc='',
                 author='', homepage='', dist_name=''):
        """插件对象

        :param alias: 插件名
        :param version: 插件版本
        :param module: 插件模块对象，它有 enable 和 disable 方法
        :param desc: 插件描述
        :param author: 插件作者
        :param homepage: 插件主页
        :param dist_name: 插件发行版名字
        """
        self.alias = alias
        # FIXME(cosven): use entry point name as plugin name, instead of the module name.
        self.name = module.__name__.split('.')[-1]
        self._module = module
        self.version = version
        self.desc = desc
        self.author = author
        self.homepage = homepage
        self.dist_name = dist_name
        self.is_enabled = False

    @classmethod
    def create(cls, module):
        """Plugin 工厂函数

        :param module:
        :return:
        """
        try:
            # alias, desc, version 为必需字段
            alias = module.__alias__
            desc = module.__desc__
            version = module.__version__  # noqa

            author = getattr(module, '__author__', '')
            homepage = getattr(module, '__homepage__', '')
            dist_name = getattr(module, '__dist_name__', '')
        except AttributeError as e:
            raise InvalidPluginError(str(e))
        else:
            return Plugin(module,
                          alias=alias,
                          desc=desc,
                          author=author,
                          homepage=homepage,
                          dist_name=dist_name)

    def init_config(self, config: Config):
        """Call plugin.init_config function if possible

        :param config: app config instance.

        .. versionadded: 3.7.15
        """
        # Define a subconfig(namespace) for plugin so that plugin can
        # define its own configuration fields.
        config.deffield(self.name,
                        type_=Config,
                        default=Config(),
                        desc=f'Configurations for plugin {self.name}')
        try:
            fn = self._module.init_config
        except AttributeError:
            # The plugin does not define any config field.
            pass
        else:
            fn(getattr(config, self.name))

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
        #: A plugin is about to enable.
        # The payload is the plugin object `(Plugin)`.
        # .. versionadded: 3.7.15
        self.about_to_enable = Signal()

    def scan(self):
        """扫描并加载插件"""
        with self._app.create_action('Scaning plugins'):
            self._scan_dirs()
            self._scan_entry_points()
        self.scan_finished.emit(list(self._plugins.values()))

    def load_module(self, module):
        """Load module and try to load the plugin"""
        with self._app.create_action('Enabling plugin:%s' % module.__name__) as action:
            # Try to create a new plugin.
            try:
                plugin = Plugin.create(module)
            except InvalidPluginError as e:
                action.failed(str(e))
                return

            # Try to init config for the plugin.
            self._plugins[plugin.name] = plugin
            try:
                plugin.init_config(self._app.config)
            except Exception as e:
                logger.exception(f'Init config for plugin:{plugin.name} failed')
                action.failed(str(e))
                return

            # Try to enbale the plugin.
            self.about_to_enable.emit(plugin)
            try:
                plugin.enable(self._app)
            except Exception as e:
                logger.exception(f'Enable plugin:{plugin.name} failed')
                action.failed(str(e))

    def _scan_dirs(self):
        """扫描插件目录中的插件"""
        module_name_list = []
        for fname in os.listdir(USER_PLUGINS_DIR):
            if os.path.isdir(os.path.join(USER_PLUGINS_DIR, fname)):
                module_name_list.append(fname)
            else:
                if fname.endswith('.py'):
                    module_name_list.append(fname[:-3])
        sys.path.append(USER_PLUGINS_DIR)
        for module_name in module_name_list:
            try:
                module = importlib.import_module(module_name)
            except Exception:  # noqa
                logger.exception('Failed to import module %s', module_name)
            else:
                self.load_module(module)

    def _scan_entry_points(self):
        """扫描通过 setuptools 机制注册的插件

        https://packaging.python.org/guides/creating-and-discovering-plugins/
        """
        try:
            import importlib.metadata
            entry_points = importlib.metadata.entry_points().get('fuo.plugins_v1', [])
        except ImportError:
            import pkg_resources
            entry_points = pkg_resources.iter_entry_points('fuo.plugins_v1')
        for entry_point in entry_points:
            try:
                module = entry_point.load()
            except Exception as e:  # noqa
                logger.exception('Failed to load module %s', entry_point.name)
            else:
                self.load_module(module)
