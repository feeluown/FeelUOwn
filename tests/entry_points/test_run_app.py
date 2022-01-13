import sys
from unittest.mock import AsyncMock

import pytest

from feeluown.entry_points.base import setup_argparse
from feeluown.entry_points.run_app import run_app


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


@pytest.fixture
def argsparser():
    return setup_argparse()


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


def test_run_app_with_cli_mode(argsparser, mocker, noharm):
    mock_load_rcfile = mocker.patch('feeluown.entry_points.run_app.fuoexec_load_rcfile')
    mock_start_app: AsyncMock = mocker.patch('feeluown.entry_points.run_app.start_app')
    mock_warnings = mocker.patch('feeluown.entry_points.run_app.warnings')

    args = argsparser.parse_args(["play", "fuo://xxx/songs/1"])
    # App must be in CliMode.
    run_app(args)

    # Warning should be ignore in cli mode because the warning can
    # pollute the output.
    mock_warnings.filterwarnings.assert_called_once_with('ignore')
    # Precheck should pass and start_app should be called.
    mock_start_app.assert_awaited()


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
