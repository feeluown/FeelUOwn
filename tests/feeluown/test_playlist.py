import asyncio
from unittest import mock

import pytest

from feeluown.library.excs import MediaNotFound
from feeluown.player import Playlist


@pytest.fixture()
def pl(app_mock, song, song1):
    """
    pl: [song, song1], current_song: song
    """
    playlist = Playlist(app_mock)
    playlist.add(song)
    playlist.add(song1)
    playlist._current_song = song
    return playlist


@pytest.fixture()
def pl_prepare_media_none(mocker, pl):
    f = asyncio.Future()
    f.set_exception(MediaNotFound())
    mocker.patch.object(Playlist, '_prepare_media', side_effect=f)


@pytest.fixture()
def pl_list_standby_return_empty(mocker, pl):
    pl._app.library.a_list_song_standby
    f2 = asyncio.Future()
    f2.set_result([])
    mock_a_list_standby = pl._app.library.a_list_song_standby
    mock_a_list_standby.return_value = f2


@pytest.fixture()
def pl_list_standby_return_song2(mocker, pl, song2):
    pl._app.library.a_list_song_standby
    f2 = asyncio.Future()
    f2.set_result([song2])
    mock_a_list_standby = pl._app.library.a_list_song_standby
    mock_a_list_standby.return_value = f2


def test_previous_song(pl, song1):
    assert pl.previous_song == song1


def test_remove_song(mocker, pl, song, song1, song2):
    # remove a nonexisting song
    pl.remove(song2)
    assert len(pl) == 2

    # remove a existing song
    pl.remove(song1)
    assert len(pl) == 1
    pl.add(song1)

    # remove a song which is marked as bad
    pl.add(song2)
    assert len(pl) == 3
    pl.mark_as_bad(song2)
    pl.remove(song2)
    assert len(pl) == 2

    # remove the current_song
    # song1 should be set as the current_song
    with mock.patch.object(Playlist, 'current_song',
                           new_callable=mock.PropertyMock) as mock_s:
        mock_s.return_value = song
        pl.remove(song)
        mock_s.assert_called_with(song1)
        assert len(pl) == 1


def test_set_current_song(pl, song2):
    # Set a nonexisting song as current song
    # The song should be inserted after current_song
    pl.pure_set_current_song(song2, None)
    assert pl.current_song == song2
    assert pl.list()[1] == song2


@pytest.mark.asyncio
async def test_set_current_song_with_bad_song_1(
        mocker, song2, pl,
        pl_prepare_media_none,
        pl_list_standby_return_empty):
    mock_pure_set_current_song = mocker.patch.object(Playlist, 'pure_set_current_song')
    mock_mark_as_bad = mocker.patch.object(Playlist, 'mark_as_bad')
    await pl.a_set_current_song(song2)
    # A song that has no valid media should be marked as bad
    assert mock_mark_as_bad.called
    # Since there is no standby song, the media should be None
    mock_pure_set_current_song.assert_called_once_with(song2, None)


@pytest.mark.asyncio
async def test_set_current_song_with_bad_song_2(
        mocker, song2, pl,
        pl_prepare_media_none,
        pl_list_standby_return_song2):
    mock_pure_set_current_song = mocker.patch.object(Playlist, 'pure_set_current_song')
    mock_mark_as_bad = mocker.patch.object(Playlist, 'mark_as_bad')
    await pl.a_set_current_song(song2)
    # A song that has no valid media should be marked as bad
    assert mock_mark_as_bad.called
    # Since there exists standby songs, the media should the url
    mock_pure_set_current_song.assert_called_once_with(song2, song2.url)


def test_pure_set_current_song(
        mocker, song, song2, pl):
    # Current song index is 0
    assert pl.list().index(song) == 0
    # song2 is not in playlist before
    pl.pure_set_current_song(song2, song2.url)
    assert pl.current_song == song2
    # The song should be inserted after the current song,
    # so the index should be 1
    assert pl.list().index(song2) == 1


@pytest.mark.asyncio
async def test_set_an_existing_bad_song_as_current_song(
        mocker, song1, song2, pl,
        pl_prepare_media_none,
        pl_list_standby_return_song2):
    """
    pl is [song, song1]
    song1 is bad, standby is [song2]
    play song1, song2 should be insert after song1 instead of song
    """
    await pl.a_set_current_song(song1)
    assert pl.list().index(song2) == 2
