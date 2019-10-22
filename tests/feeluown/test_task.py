import asyncio
import time
from unittest import mock

import pytest

from feeluown.task import TaskManager, PreemptiveTaskSpec


@pytest.mark.asyncio
async def test_task_manager(app_mock):
    loop = asyncio.get_event_loop()
    task_mgr = TaskManager(app_mock, loop)
    task_spec = task_mgr.get_or_create('fetch-song-standby')

    async def fetch_song():
        pass

    mock_done_cb = mock.MagicMock()
    task = task_spec.bind_coro(fetch_song())
    task.add_done_callback(mock_done_cb)
    await asyncio.sleep(0.1)  # let task run
    assert mock_done_cb.called is True


@pytest.mark.asyncio
async def test_preemptive_task_spec_bind_coro():
    mgr = mock.MagicMock()
    loop = asyncio.get_event_loop()
    mgr.loop = loop
    task_spec = PreemptiveTaskSpec(mgr, 'fetch-song-standby')

    mock_cancelled_cb = mock.MagicMock()

    async def fetch_song():
        try:
            await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            mock_cancelled_cb()

    task_spec.bind_coro(fetch_song())
    await asyncio.sleep(0.1)  # let fetch_song run
    await task_spec.bind_coro(fetch_song())
    assert mock_cancelled_cb.called is True
