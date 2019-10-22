import asyncio
from unittest import mock

import pytest

from feeluown.player import Playlist, Player
from tests.helpers import is_travis_env


@pytest.mark.filterwarnings('ignore:coroutine')
@pytest.mark.asyncio
async def test_set_cursong_in_non_mainthread(app_mock, song):
    pl = Playlist(app_mock)

    def set_in_non_mainthread():
        pl.current_song = song

    loop = asyncio.get_event_loop()
    try:
        # make song url invalid
        song.url = ''
        # playlist should create a asyncio task to fetch a standby
        # set current song in non mainthread
        await loop.run_in_executor(None, set_in_non_mainthread)
    except RuntimeError:
        pytest.fail('Set current song in non mainthread should work')


@pytest.mark.skipif(is_travis_env, reason="this may fail")
@pytest.mark.filterwarnings('ignore:coroutine')
@pytest.mark.asyncio
async def test_prepare_media(app_mock, song):
    player = Player(app_mock)
    mock_func = mock.MagicMock()
    player.prepare_media(song, mock_func)
    # this may fail, since we should probably wait a little bit longer
    await asyncio.sleep(0.1)
    assert mock_func.called is True


@pytest.mark.filterwarnings('ignore:coroutine')
@pytest.mark.asyncio
async def test_prepare_media_in_non_mainthread(app_mock, song):
    player = Player(app_mock)
    loop = asyncio.get_event_loop()
    mock_func = mock.MagicMock()
    try:
        await loop.run_in_executor(
            None, player.prepare_media, song, mock_func)
    except RuntimeError:
        pytest.fail('Prepare media in non mainthread should work')
