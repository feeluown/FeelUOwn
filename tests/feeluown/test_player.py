import asyncio
import threading

import pytest

from feeluown.player import Playlist


async def a_list_song_standby(song):
    pass


@pytest.mark.filterwarnings('ignore:coroutine')
@pytest.mark.asyncio
async def test_set_cursong_in_non_mainthread(app_mock, song):
    app_mock.library.a_list_song_standby = a_list_song_standby
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
