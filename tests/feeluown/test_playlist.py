from unittest import mock

import pytest

from feeluown.player import Playlist


@pytest.fixture()
def pl(app_mock, song, song1):
    playlist = Playlist(app_mock)
    playlist.add(song)
    playlist.add(song1)
    playlist._current_song = song
    return playlist


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
