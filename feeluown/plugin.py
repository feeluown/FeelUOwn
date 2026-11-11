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


def _env_flag(name):
    """Case-insensitive env truth check (1/true/yes)."""
    return os.getenv(name, '').strip().lower() in ('1', 'true', 'yes')


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
        """Plugin object

        :param alias: plugin name
        :param version: plugin version
        :param module: plugin module object, which has enable and disable methods
        :param desc: plugin description
        :param author: plugin author
        :param homepage: plugin homepage
        :param dist_name: plugin distribution name
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
        """Plugin factory function

        :param module:
        :return:
        """
        try:
            # alias, desc, version are required fields
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
        # scan_finished is emitted after enabling is done. The payload is
        # the full list of scanned plugins (same as before); skipped/failed
        # ones remain with is_enabled=False so existing receivers that
        # expect the full list keep working.
        # TODO: maybe rename scan_finished to plugins_enabled?
        self.scan_finished = Signal()

    def light_scan(self):
        """Scan plugins without enabling them."""
        # Allow skipping all plugin scans for fast startup/bench/debugging.
        # Env: FEELUOWN_NO_PLUGINS=1
        if _env_flag('FEELUOWN_NO_PLUGINS'):
            logger.info('Skip light scan plugins (FEELUOWN_NO_PLUGINS is set).')
            return
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
        import time

        # Honor the flag here too: the manager is a singleton, so an
        # in-process reuse (tests, fuoexec) may hold stale _plugins entries
        # from an earlier scan even when the current run asked to skip.
        if _env_flag('FEELUOWN_NO_PLUGINS'):
            logger.info('Skip enable plugins (FEELUOWN_NO_PLUGINS is set).')
            self.scan_finished.emit([])
            return

        # Optional allowlist: FEELUOWN_PLUGINS="foo,bar" only enables those.
        allowlist_raw = os.getenv('FEELUOWN_PLUGINS', '').strip()
        allowlist = (
            {name.strip() for name in allowlist_raw.split(',') if name.strip()}
            if allowlist_raw else None
        )
        logger.info(f'Enable plugins that are scaned. total: {len(self._plugins)} ')
        for plugin in self._plugins.values():
            if allowlist is not None and not self._in_allowlist(plugin, allowlist):
                logger.info(f'Skip enabling plugin:{plugin.name} (not in allowlist)')
                continue
            # Try to enbale the plugin.
            self.about_to_enable.emit(plugin)
            start = time.perf_counter()
            try:
                plugin.enable(app)
            except Exception:  # noqa
                logger.exception(f'Enable plugin:{plugin.name} failed')
            else:
                cost_ms = (time.perf_counter() - start) * 1000
                if cost_ms > 50:
                    logger.warning(
                        f'Enable plugin:{plugin.name} took {cost_ms:.1f}ms')
        # Preserve historic payload: all scanned plugins, so external
        # receivers expecting the full list keep working. Use
        # plugin.is_enabled to tell enabled from skipped/failed.
        self.scan_finished.emit(list(self._plugins.values()))

    @staticmethod
    def _in_allowlist(plugin, allowlist):
        """Check name/alias against allowlist, with fuo_/feeluown_ stripped."""
        candidates = {plugin.name, plugin.alias}
        if plugin.name.startswith('fuo_'):
            candidates.add(plugin.name[4:])
        elif plugin.name.startswith('feeluown_'):
            candidates.add(plugin.name[9:])
        return bool(candidates & allowlist)

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
        """Scan the plugins in the plugin directory.

        Underscore/dot-prefixed files and dirs are treated as private
        helpers (e.g. ``_utils.py``, editor backups), not plugins, and are
        skipped to avoid pointless imports on startup.
        """
        if not os.path.exists(USER_PLUGINS_DIR):
            return

        module_name_list = []
        for fname in os.listdir(USER_PLUGINS_DIR):
            # Skip hidden/private files to avoid importing editor backups
            # and private helpers (e.g. ``_utils.py``) on startup.
            if fname.startswith(('.', '_')):
                continue
            if os.path.isdir(os.path.join(USER_PLUGINS_DIR, fname)):
                module_name_list.append(fname)
            else:
                if fname.endswith('.py'):
                    module_name_list.append(fname[:-3])
        if USER_PLUGINS_DIR not in sys.path:
            sys.path.append(USER_PLUGINS_DIR)
        for module_name in module_name_list:
            try:
                module = importlib.import_module(module_name)
            except Exception:  # noqa
                logger.exception('Failed to import module %s', module_name)
            else:
                self.load_plugin_from_module(module)

    def _scan_entry_points(self):
        """Scan plugins registered via the setuptools mechanism

        https://packaging.python.org/guides/creating-and-discovering-plugins/
        """
        import time

        start = time.perf_counter()
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
        cost_ms = (time.perf_counter() - start) * 1000
        logger.info(f'Scan entry points finished in {cost_ms:.1f}ms')


plugins_mgr = PluginsManager()
