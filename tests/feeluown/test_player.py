from unittest import mock

import pytest

from fuocore.playlist import PlaybackMode
from feeluown.utils.dispatch import Signal
from feeluown.player import Playlist, PlaylistMode, Player


@pytest.fixture
def mock_a_set_cursong(mocker):
    mocker.patch.object(Playlist, 'a_set_current_song', new=mock.MagicMock)


@pytest.mark.asyncio
async def test_playlist_change_mode(app_mock, mocker):
    # from normal to fm
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    assert pl.playback_mode is PlaybackMode.sequential

    # from fm to normal
    pl.mode = PlaylistMode.normal
    assert pl.mode is PlaylistMode.normal


@pytest.mark.asyncio
async def test_playlist_exit_fm_mode(app_mock, song, mocker,
                                     mock_a_set_cursong):
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    pl.current_song = song
    assert pl.mode is PlaylistMode.normal
    assert app_mock.task_mgr.get_or_create.called


@pytest.mark.asyncio
async def test_playlist_fm_mode_play_next(app_mock, song, song1,
                                          mock_a_set_cursong):
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    pl.fm_add(song1)
    pl.fm_add(song)
    pl._current_song = song1
    pl.current_song = song   # should not exit fm mode
    assert pl.mode is PlaylistMode.fm


@pytest.mark.asyncio
async def test_playlist_fm_mode_play_previous(app_mock, song, song1,
                                              mock_a_set_cursong):
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    pl.fm_add(song1)
    pl.fm_add(song)
    pl._current_song = song
    pl.current_song = song1  # should not exit fm mode
    assert pl.mode is PlaylistMode.fm


@pytest.mark.asyncio
async def test_playlist_eof_reached(app_mock, song, mocker,
                                    mock_a_set_cursong):
    mock_emit = mocker.patch.object(Signal, 'emit')
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    pl.next()  # first emit
    pl.fm_add(song)
    # assume current_song is song
    pl._current_song = song
    pl.next()  # second emit
    mock_emit.assert_has_calls([
        mock.call(PlaybackMode.sequential),
        mock.call(PlaylistMode.fm),
        mock.call(),
        mock.call(0, 1),  # songs_added
        mock.call()
    ])


@pytest.mark.asyncio
async def test_playlist_resumed_from_eof_reached(app_mock, song, mocker,
                                                 mock_a_set_cursong):
    mock_set_current_song = mocker.patch.object(Playlist, 'set_current_song')
    pl = Playlist(app_mock)

    def feed_playlist():
        pl.fm_add(song)
        pl.next()

    pl.eof_reached.connect(feed_playlist)
    pl.mode = PlaylistMode.fm
    pl.next()
    mock_set_current_song.assert_has_calls([mock.call(song)])


@pytest.mark.asyncio
async def test_playlist_remove_current_song(app_mock):
    pass


@pytest.mark.asyncio
async def test_play_next_bad_song(app_mock, song, song1, mocker):
    """
    Prepare media for song raises unknown error, the song should
    be marked as bad.
    """
    pl = Playlist(app_mock)
    mocker.patch.object(pl, '_prepare_media', side_effect=Exception())
    mock_mark_as_bad = mocker.patch.object(pl, 'mark_as_bad')
    mock_next = mocker.patch.object(pl, 'next')
    pl.add(song)
    pl.add(song1)
    pl._current_song = song
    await pl.a_set_current_song(pl.next_song)
    assert mock_mark_as_bad.called
    assert mock_next.called


def test_play_all(app_mock):
    player = Player()
    playlist = Playlist(app_mock)
    player.set_playlist(playlist)
    playlist.mode = PlaylistMode.fm
    playlist.set_models([], next_=True)
    assert playlist.mode == PlaylistMode.normal


def test_change_song(app_mock, mocker, song, song1):
    mocker.patch.object(Player, 'play')
    pl = Playlist(app_mock)
    pl.add(song)
    pl._current_song = song
    player = Player()
    player.set_playlist(pl)
    with mock.patch.object(Playlist, 'current_song',
                           new_callable=mock.PropertyMock) as mock_s:
        mock_s.return_value = song  # return current song
        player.play_song(song1)
        pl.next()
        assert pl.current_song == song
