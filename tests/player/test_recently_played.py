import pytest

from feeluown.player import RecentlyPlayed, Playlist


@pytest.fixture()
def playlist(app_mock):
    playlist = Playlist(app_mock)
    return playlist


def test_list_songs(playlist, song1, song2):
    recently_played = RecentlyPlayed(playlist)
    playlist.song_changed_v2.emit(song1, object())
    playlist.song_changed_v2.emit(song2, object())
    songs = recently_played.list_songs()
    assert len(songs) == 2
    assert songs[0] == song2
