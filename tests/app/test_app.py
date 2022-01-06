import argparse
from unittest import skip

import pytest

from feeluown.app import (
    create_app,
    init_args_parser,
    create_config,
    AppMode,
)


@pytest.fixture
def argsparser():
    parser = argparse.ArgumentParser()
    init_args_parser(parser)

    # Simulate cli subparser.
    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.add_parser('test')
    return parser


@pytest.fixture
def args(argsparser):
    return argsparser.parse_args(args=[])


@pytest.fixture
def args_test(argsparser):
    return argsparser.parse_args(args=['test'])


@skip("No easy way to simulate QEventLoop.")
@pytest.mark.asyncio
async def test_create_gui_app(args):
    pass


@pytest.mark.asyncio
async def test_create_server_app(args):
    config = create_config()
    config.MODE = AppMode.server
    app = create_app(args, config=config)
    assert app.has_server and not app.has_gui


@pytest.mark.asyncio
async def test_create_cli_app(args_test):
    config = create_config()
    config.MODE = AppMode.cli
    app = create_app(args_test, config=config)
    assert not app.has_server and not app.has_gui
