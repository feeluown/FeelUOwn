import pytest

from feeluown.argparser import create_cli_parser
from feeluown.app import create_config
from feeluown.plugin import PluginsManager
from feeluown.gui.uimodels.collection import CollectionUiManager
from feeluown.utils.dispatch import Signal


@pytest.fixture
@pytest.mark.asyncio
async def signal_aio_support():
    Signal.setup_aio_support()
    yield
    Signal.teardown_aio_support()


@pytest.fixture
def argsparser():
    parser = create_cli_parser()
    return parser


@pytest.fixture
def args_test(argsparser):
    return argsparser.parse_args(args=[])


@pytest.fixture
def args(argsparser):
    return argsparser.parse_args(args=[])


@pytest.fixture
def config():
    return create_config()


@pytest.fixture
def noharm(mocker):
    mocker.patch('feeluown.app.app.Player')
    mocker.patch.object(PluginsManager, 'scan')
    # CollectionUiManager write library.fuo file during initialization.
    mocker.patch.object(CollectionUiManager, 'initialize')
