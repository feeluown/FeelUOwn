from __future__ import annotations
import importlib
import logging
import os
import sys
from typing import TYPE_CHECKING

from feeluown.config import Config
from feeluown.utils.dispatch import Signal
from .consts import USER_PLUGINS_DIR

if TYPE_CHECKING:
    from feeluown.app import App


__all__ = (
    'plugins_mgr',
    'Plugin',
)

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
    # pylint: disable=too-many-positional-arguments
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
        # pylint: disable=too-many-arguments

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
            _ = module.__version__  # noqa

            author = getattr(module, '__author__', '')
            homepage = getattr(module, '__homepage__', '')
            dist_name = getattr(module, '__dist_name__', '')
        except AttributeError as e:
            raise InvalidPluginError(str(e)) from None
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
        myconfig = Config(name=self.name, parent=config)

        names = [self.name]
        # Currently, plugin name looks like fuo_xxx and xxx is the real name.
        # User maye want to define config like app.xxx.X=Y,
        # instead of app.fuo_xxx.X=Y.
        if self.name.startswith('fuo_'):
            names.append(self.name[4:])
        elif self.name.startswith('feeluown_'):
            names.append(self.name[9:])

        # Define a subconfig(namespace) for plugin so that plugin can
        # define its own configuration fields.
        for name in names:
            config.deffield(name,
                            type_=Config,
                            default=myconfig,
                            desc=f'Configurations for plugin {self.name}')

        try:
            fn = self._module.init_config
        except AttributeError:
            # The plugin does not define any config field.
            pass
        else:
            fn(myconfig)

    def enable(self, app):
        self._module.enable(app)
        self.is_enabled = True

    def disable(self, app):
        self._module.disable(app)
        self.is_enabled = False


class PluginsManager:
    def __init__(self):
        self._plugins = {}
        #: A plugin is about to enable.
        # The payload is the plugin object `(Plugin)`.
        # .. versionadded: 3.7.15
        self.about_to_enable = Signal()
        # scan_finished means all found plugins are enabled.
        # TODO: maybe rename scan_finished to plugins_enabled?
        self.scan_finished = Signal()

    def light_scan(self):
        """Scan plugins without enabling them."""
        logger.info('Light scan plugins.')
        self._scan_dirs()
        self._scan_entry_points()

    def init_plugins_config(self, config):
        """Try to init config for the plugin.

        Plugin can declare their configuration items.
        """
        for plugin in self._plugins.values():
            try:
                plugin.init_config(config)
            except Exception:  # noqa
                logger.exception(f'Init config for plugin:{plugin.name} failed')

    def enable_plugins(self, app: App):
        logger.info(f'Enable plugins that are scaned. total: {len(self._plugins)} ')
        for plugin in self._plugins.values():
            # Try to enbale the plugin.
            self.about_to_enable.emit(plugin)
            try:
                plugin.enable(app)
            except Exception:  # noqa
                logger.exception(f'Enable plugin:{plugin.name} failed')
        self.scan_finished.emit(list(self._plugins.values()))

    def load_plugin_from_module(self, module):
        """Load module and try to load the plugin"""
        logger.info('Try to load plugin from module: %s', module.__name__)

        # Try to create a new plugin.
        try:
            plugin = Plugin.create(module)
        except InvalidPluginError:
            return
        self._plugins[plugin.name] = plugin

    def _scan_dirs(self):
        """扫描插件目录中的插件"""
        if not os.path.exists(USER_PLUGINS_DIR):
            return

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
                self.load_plugin_from_module(module)

    def _scan_entry_points(self):
        """扫描通过 setuptools 机制注册的插件

        https://packaging.python.org/guides/creating-and-discovering-plugins/
        """
        try:
            import importlib.metadata  # pylint: disable=redefined-outer-name
            try:
                entry_points = importlib.metadata.entry_points() \
                    .select(group='fuo.plugins_v1')
            except AttributeError:  # old version does not has `select` method
                entry_points = importlib.metadata.entry_points() \
                    .get('fuo.plugins_v1', [])  # pylint: disable=no-member
        except ImportError:
            import pkg_resources
            entry_points = pkg_resources.iter_entry_points('fuo.plugins_v1')
        for entry_point in entry_points:
            try:
                module = entry_point.load()
            except Exception:  # noqa
                logger.exception('Failed to load module %s', entry_point.name)
            else:
                self.load_plugin_from_module(module)


plugins_mgr = PluginsManager()
