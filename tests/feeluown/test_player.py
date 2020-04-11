import asyncio
from unittest import mock

import pytest

from fuocore.playlist import PlaybackMode
from fuocore.dispatch import Signal
from feeluown.player import Playlist, Player, PlaylistMode
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


@pytest.mark.asyncio
async def test_playlist_change_mode(app_mock, mocker):
    mock_clear = mocker.patch.object(Playlist, 'clear')
    # from normal to fm
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    mock_clear.assert_called_once_with()
    assert pl.playback_mode is PlaybackMode.sequential

    # from fm to normal
    pl.mode = PlaylistMode.normal
    assert pl.mode is PlaylistMode.normal


@pytest.mark.asyncio
async def test_playlist_exit_fm_mode(app_mock, song, mocker):
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    pl.current_song = song
    assert pl.mode is PlaylistMode.normal
    assert app_mock.task_mgr.get_or_create.called


@pytest.mark.asyncio
async def test_playlist_fm_mode_play_next(app_mock, song, song1, mocker):
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    pl.fm_add(song1)
    pl.fm_add(song)
    pl._current_song = song1
    pl.current_song = song   # should not exit fm mode
    assert pl.mode is PlaylistMode.fm


@pytest.mark.asyncio
async def test_playlist_fm_mode_play_previous(app_mock, song, song1, mocker):
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    pl.fm_add(song1)
    pl.fm_add(song)
    pl._current_song = song
    pl.current_song = song1  # should not exit fm mode
    assert pl.mode is PlaylistMode.fm


@pytest.mark.asyncio
async def test_playlist_eof_reached(app_mock, song, mocker):
    mock_emit = mocker.patch.object(Signal, 'emit')
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    pl.next()  # first emit
    pl.fm_add(song)
    # assume current_song is song
    pl._current_song = song
    pl.next()  # second emit
    mock_emit.assert_has_calls([
        mock.call(),
        mock.call(),
    ])


@pytest.mark.asyncio
async def test_playlist_resumed_from_eof_reached(app_mock, song, mocker):
    mock_current_song = mocker.patch.object(Playlist, 'current_song')
    mock_set = mocker.MagicMock()
    mock_current_song.__get__ = mocker.MagicMock(return_value=None)
    mock_current_song.__set__ = mock_set
    pl = Playlist(app_mock)

    def feed_playlist():
        pl.fm_add(song)
        pl.next()

    pl.eof_reached.connect(feed_playlist)
    pl.mode = PlaylistMode.fm
    pl.next()
    mock_set.assert_has_calls([mock.call(pl, song)])


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
    pl = Playlist(app_mock)
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, pl.prepare_media, song)
    except RuntimeError:
        pytest.fail('Prepare media in non mainthread should work')
