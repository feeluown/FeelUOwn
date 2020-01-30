import asyncio
from unittest import mock

import pytest

from fuocore.dispatch import Signal
from feeluown.fuoexec import SignalsSlotsManager


@pytest.fixture
def signal():
    return Signal()


@pytest.mark.asyncio
async def test_signals_slots_mgr(app_mock, signal):
    signals_slots_mgr = SignalsSlotsManager()
    Signal.setup_aio_support()
    func = mock.MagicMock()
    app_mock.test_signal = signal

    # test if add method works
    signals_slots_mgr.add('app.test_signal', func)
    signals_slots_mgr.initialize(app_mock)
    signal.emit()
    await asyncio.sleep(0.1)  # schedule signal callbacks with aioqueue enabled
    assert func.called is True

    # test if add method works after initialized
    func_lator = mock.MagicMock()
    signals_slots_mgr.add('app.test_signal', func_lator)
    signal.emit()
    await asyncio.sleep(0.1)
    assert func_lator.called is True

    # test if remove method works
    signals_slots_mgr.remove('app.test_signal', func_lator)
    signal.emit()
    await asyncio.sleep(0.1)
    assert func_lator.call_count == 1
    assert func.call_count == 3
    Signal.teardown_aio_support()


@pytest.mark.asyncio
async def test_signals_slots_mgr_add_slot_symbol(app_mock, signal, mocker):
    """
    test add slot symbol
    """
    signals_slots_mgr = SignalsSlotsManager()
    signals_slots_mgr.initialize(app_mock)
    Signal.setup_aio_support()
    app_mock.test_signal = signal

    func = mock.MagicMock()
    func.__name__ = 'fake_func'
    mock_F = mocker.patch('feeluown.fuoexec.fuoexec_F',
                          return_value=func)
    signals_slots_mgr.add('app.test_signal', 'fake_func')

    signal.emit()
    await asyncio.sleep(0.1)
    mock_F.assert_called_once_with('fake_func')
    assert func.called is True
    Signal.teardown_aio_support()
