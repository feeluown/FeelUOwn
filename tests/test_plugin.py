from importlib.util import spec_from_file_location, module_from_spec

import pytest

from feeluown.config import Config
from feeluown.plugin import Plugin, PluginsManager


foo_py_content = """
__alias__ = 'FOO'
__desc__ = ''
__version__ = '0.1'


def init_config(config):
    config.deffield('VERBOSE', type_=int, default=0)
"""


@pytest.fixture
def foo_module(tmp_path):
    pyfile = tmp_path / 'foo.py'
    pyfile.touch()
    with pyfile.open('w') as f:
        f.write(foo_py_content)
    spec = spec_from_file_location('foo', pyfile)
    assert spec is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def foo_plugin(foo_module):
    return Plugin.create(foo_module)


@pytest.fixture
def plugin_mgr(app_mock):
    return PluginsManager(app_mock)


def test_plugin_init_config(foo_plugin):
    config = Config()
    foo_plugin.init_config(config)
    # `config.foo` should be created and foo.VERBOSE should be equal to 0.
    assert config.foo.VERBOSE == 0


def test_plugin_manager_load_module(plugin_mgr, foo_module, mocker):
    mock_init_config = mocker.patch.object(Plugin, 'init_config')
    mock_enable = mocker.patch.object(Plugin, 'enable')
    plugin_mgr.load_module(foo_module)
    # The `init_config` and `enable` function should be called.
    assert mock_init_config.called
    assert mock_enable.called
