import asyncio

import pytest

from feeluown.excs import ProviderIOError
from feeluown.player import Playlist, PlaylistMode, FM, MetadataAssembler
from feeluown.task import TaskManager


def test_fm_activate_and_deactivate(app_mock, song, mocker):
    mock_fetch = mocker.MagicMock(return_value=[song])
    app_mock.playlist = Playlist(app_mock)
    fm = FM(app_mock)
    fm.activate(mock_fetch)
    assert app_mock.playlist.mode is PlaylistMode.fm
    assert app_mock.task_mgr.get_or_create.called

    fm.deactivate()
    assert app_mock.playlist.mode is PlaylistMode.normal


def test_when_playlist_fm_mode_exited(app_mock, song, mocker):
    mock_fetch = mocker.MagicMock()
    app_mock.playlist = Playlist(app_mock)
    fm = FM(app_mock)
    fm.activate(mock_fetch)
    app_mock.playlist.mode = PlaylistMode.normal
    assert fm._activated is False  # noqa


@pytest.mark.asyncio
async def test_fetch_song_cancelled(app_mock, song, mocker):
    mock_fetch = mocker.MagicMock()
    app_mock.playlist = Playlist(app_mock)
    app_mock.task_mgr = TaskManager(app_mock)
    fm = FM(app_mock)
    fm.activate(mock_fetch)
    task_spec = app_mock.task_mgr.get_or_create(fm._fetch_songs_task_name)
    task_spec._task.cancel()
    await asyncio.sleep(0.1)  # schedule cancel callback
    assert fm._is_fetching_songs is False


@pytest.mark.asyncio
async def test_fetch_song_failed(app_mock, song, mocker):
    mock_fetch = mocker.MagicMock(side_effect=ProviderIOError)
    mock_fm_add = mocker.patch.object(Playlist, 'fm_add')
    app_mock.playlist = Playlist(app_mock)
    app_mock.task_mgr = TaskManager(app_mock)
    fm = FM(app_mock)
    fm.activate(mock_fetch)
    assert fm._is_fetching_songs is True
    await asyncio.sleep(0.1)  # schedule mock_fetch callback
    assert fm._is_fetching_songs is False
    assert not mock_fm_add.called


@pytest.mark.asyncio
async def test_multiple_eof_reached_signal(app_mock, song, mocker):
    mock_fetch = mocker.MagicMock(return_value=[song] * 3)
    mock_fm_add = mocker.patch.object(Playlist, 'fm_add')
    app_mock.playlist = Playlist(app_mock)
    app_mock.task_mgr = TaskManager(app_mock)
    fm = FM(app_mock)
    fm.activate(mock_fetch)
    app_mock.playlist.next()
    app_mock.playlist.next()
    task_spec = app_mock.task_mgr.get_or_create(fm._fetch_songs_task_name)
    await task_spec._task  # this is a little bit tricky
    # called exactly once
    mock_fetch.assert_called_once_with(3)
    assert mock_fm_add.called


@pytest.mark.asyncio
async def test_reactivate_fm_mode_after_playing_other_songs(
        app_mock, song, song1, mocker):

    mocker.patch.object(MetadataAssembler, 'prepare_for_song')

    def f(*args, **kwargs): return [song1]

    def is_active(fm): return fm.is_active

    app_mock.task_mgr = TaskManager(app_mock)
    playlist = Playlist(app_mock)
    app_mock.playlist = playlist
    fm = FM(app_mock)
    fm.activate(f)
    assert playlist.mode is PlaylistMode.fm
    await asyncio.sleep(0.1)  # wait for fm-fetch-song task finished

    # user trigger play next
    await app_mock.playlist.a_set_current_song(song)
    assert playlist.mode is PlaylistMode.normal
    assert is_active(fm) is False

    await asyncio.sleep(0.1)  # wait for validate-song task finished
    assert playlist.list() == [song]

    fm.activate(f)
    assert is_active(fm) is True
    assert playlist.mode is PlaylistMode.fm
