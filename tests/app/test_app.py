from unittest import skip

import pytest

from feeluown.app import create_app, AppMode


@skip("No easy way to simulate QEventLoop.")
@pytest.mark.asyncio
async def test_create_gui_app(args):
    pass


@pytest.mark.asyncio
async def test_create_server_app(args, config):
    config.MODE = AppMode.server
    app = create_app(args, config=config)
    assert app.has_server and not app.has_gui


@pytest.mark.asyncio
async def test_create_cli_app(args_test, config,
                              no_player):
    config.MODE = AppMode.cli
    app = create_app(args_test, config=config)
    assert not app.has_server and not app.has_gui
