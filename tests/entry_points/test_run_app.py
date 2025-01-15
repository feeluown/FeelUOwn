import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from feeluown.argparser import create_cli_parser
from feeluown.collection import CollectionManager
from feeluown.entry_points.run_app import run_app, before_start_app, start_app
from feeluown.app import App, AppMode, get_app
from feeluown.app.cli_app import CliApp
from feeluown.plugin import PluginsManager
from feeluown.version import VersionManager


@pytest.fixture
def noqt():
    """
    HACK: Remove PyQt5 from modules before testcase starts.
    """
    old = sys.modules.get('PyQt5')
    if old is not None:
        sys.modules.pop('PyQt5')
        yield
        sys.modules['PyQt5'] = old


@pytest.fixture
def noharm(mocker):
    """
    Do not write or update any file on the system.
    """
    mocker.patch('feeluown.entry_points.run_app.ensure_dirs')
    mocker.patch.object(App, 'dump_state')
    mocker.patch.object(PluginsManager, 'enable_plugins')
    # CollectionManager write library.fuo file during scaning.
    mocker.patch.object(CollectionManager, 'scan')


@pytest.fixture
def argsparser():
    return create_cli_parser()


def test_before_start_app_with_default_args(argsparser, mocker, noharm):
    mocker.patch('feeluown.entry_points.run_app.fuoexec_load_rcfile')
    mocker.patch('feeluown.entry_points.run_app.precheck')
    mock_asyncio = mocker.patch('feeluown.entry_points.run_app.asyncio')
    args = argsparser.parse_args([])
    _, config = before_start_app(args)
    assert mock_asyncio.set_event_loop_policy.called
    assert AppMode.gui in AppMode(config.MODE)


def test_run_app_with_no_window_mode(argsparser, mocker, noqt, noharm):
    mock_load_rcfile = mocker.patch('feeluown.entry_points.run_app.fuoexec_load_rcfile')
    mock_precheck = mocker.patch('feeluown.entry_points.run_app.precheck')
    mock_start_app: AsyncMock = mocker.patch('feeluown.entry_points.run_app.start_app')

    args = argsparser.parse_args(["-nw"])
    run_app(args)

    # rcfile should be loaded.
    mock_load_rcfile.assert_called()
    # precheck should be called.
    mock_precheck.assert_called()
    # start_app should be called.
    mock_start_app.assert_awaited()

    # PyQt5 should not be imported during the startup.
    assert 'PyQt5' not in sys.modules


@pytest.mark.asyncio
async def test_start_app(argsparser, mocker, noharm):
    VersionManager.check_release = MagicMock(return_value=asyncio.Future())
    mocker.patch('feeluown.entry_points.run_app.fuoexec_load_rcfile')
    # fuoexec_init can be only called once, mock it here.
    mocker.patch('feeluown.entry_points.run_app.fuoexec_init')
    mocker.patch('feeluown.entry_points.run_app.warnings')
    # setup_logger may set logger output to file (~/.FeelUown/stdout.log),
    # but the directory may not exist on CI. It must be mocked.
    mocker.patch('feeluown.entry_points.run_app.setup_logger')
    mock_app_run = mocker.patch.object(CliApp, 'run')

    # Run app with CliMode.
    args = argsparser.parse_args(["play", "fuo://xxx/songs/1"])
    args, config = before_start_app(args)
    future = asyncio.Future()
    future.set_result(None)
    await start_app(args, config, future)
    get_app().exit()

    mock_app_run.assert_called_once_with()


def test_server_already_started(argsparser, mocker, noharm):
    class XE(Exception):
        pass

    mocker.patch('feeluown.entry_points.run_app.fuoexec_load_rcfile')
    mock_sys = mocker.patch('feeluown.entry_points.run_app.sys')

    mock_sys.exit.side_effect = XE()
    mock_is_port_inuse = mocker.patch('feeluown.entry_points.run_app.is_port_inuse')
    mock_start_app: AsyncMock = mocker.patch('feeluown.entry_points.run_app.start_app')
    mock_is_port_inuse.return_value = True

    args = argsparser.parse_args(["-nw"])
    # Precheck failed, sys.exit should be called.
    with pytest.raises(XE):
        run_app(args)
    mock_start_app.assert_not_awaited()
