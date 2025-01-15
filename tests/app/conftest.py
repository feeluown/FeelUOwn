import asyncio
from unittest import mock

import pytest
import pytest_asyncio

from feeluown.argparser import create_cli_parser
from feeluown.app import create_config
from feeluown.plugin import PluginsManager
from feeluown.collection import CollectionManager
from feeluown.utils.dispatch import Signal
from feeluown.player import PlayerPositionDelegate


@pytest_asyncio.fixture
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
    mocker.patch.object(PluginsManager, 'enable_plugins')
    mocker.patch.object(CollectionManager, 'scan')
    # To avoid resource leak::
    #   RuntimeWarning: coroutine 'xxx' was never awaited
    PlayerPositionDelegate.start = mock.MagicMock(return_value=asyncio.Future())
