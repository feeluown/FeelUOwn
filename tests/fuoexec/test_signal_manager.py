import asyncio
from unittest import mock

import pytest

from feeluown.utils.dispatch import Signal
from feeluown.fuoexec.signal_manager import SignalManager


@pytest.fixture
def signal():
    return Signal()


@pytest.fixture
def signal_mgr():
    return SignalManager()


@pytest.mark.asyncio
async def test_add_and_remove(app_mock, signal_mgr, signal):
    Signal.setup_aio_support()
    func = mock.MagicMock()
    app_mock.test_signal = signal

    # test if add method works
    signal_mgr.add('app.test_signal', func, use_symbol=False)
    signal_mgr.initialize(app_mock)
    signal.emit()
    await asyncio.sleep(0.1)  # schedule signal callbacks with aioqueue enabled
    assert func.called is True


@pytest.mark.asyncio
async def test_add_and_remove_after_initialization(app_mock, signal_mgr, signal):
    Signal.setup_aio_support()
    # test if add method works after initialized
    func_lator = mock.MagicMock()
    app_mock.test_signal = signal
    signal_mgr.initialize(app_mock)
    signal_mgr.add('app.test_signal', func_lator, use_symbol=False)
    signal.emit()
    await asyncio.sleep(0.1)
    assert func_lator.called is True

    # test if remove method works
    signal_mgr.remove('app.test_signal', func_lator, use_symbol=False)
    signal.emit()
    await asyncio.sleep(0.1)
    assert func_lator.call_count == 1
    Signal.teardown_aio_support()


@pytest.mark.asyncio
async def test_add_and_remove_symbol(app_mock, signal_mgr, signal, mocker):
    """
    test add slot symbol
    """
    signal_mgr.initialize(app_mock)

    Signal.setup_aio_support()
    app_mock.test_signal = signal

    func = mock.MagicMock()
    func.__name__ = 'fake_func'
    mock_F = mocker.patch('feeluown.fuoexec.signal_manager.fuoexec_F',
                          return_value=func)
    signal_mgr.add('app.test_signal', func, use_symbol=True)
    signal.emit()
    await asyncio.sleep(0.1)
    mock_F.assert_called_once_with('fake_func')
    # fuoexec_F should be called once.
    assert func.called
    assert func.call_count == 1

    signal_mgr.remove('app.test_signal', func, use_symbol=True)
    signal.emit()
    await asyncio.sleep(0.1)
    # fuoexec_F should not be called anymore
    assert func.call_count == 1

    Signal.teardown_aio_support()
