import argparse
import pytest

from feeluown.app import init_args_parser, create_config
from feeluown.utils.dispatch import Signal


@pytest.fixture
@pytest.mark.asyncio
async def signal_aio_support():
    Signal.setup_aio_support()
    yield
    Signal.teardown_aio_support()


@pytest.fixture
def argsparser():
    parser = argparse.ArgumentParser()
    init_args_parser(parser)

    # Simulate cli subparser.
    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.add_parser('test')
    return parser


@pytest.fixture
def args_test(argsparser):
    return argsparser.parse_args(args=['test'])


@pytest.fixture
def args(argsparser):
    return argsparser.parse_args(args=[])


@pytest.fixture
def config():
    return create_config()


@pytest.fixture
def no_player(mocker):
    mocker.patch('feeluown.app.app.Player')
