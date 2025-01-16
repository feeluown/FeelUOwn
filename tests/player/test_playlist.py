import asyncio
from unittest import mock

import pytest
import pytest_asyncio

from feeluown.library.excs import MediaNotFound
from feeluown.player import (
    Playlist, PlaylistMode, Player, PlaybackMode,
    PlaylistRepeatMode, PlaylistShuffleMode, MetadataAssembler
)
from feeluown.utils.dispatch import Signal

SONG2_URL = 'http://x.mp3'


@pytest.fixture()
def pl(app_mock, song, song1):
    """
    pl: [song, song1], current_song: song
    """
    app_mock.config.ENABLE_MV_AS_STANDBY = 0
    playlist = Playlist(app_mock)
    playlist.add(song)
    playlist.add(song1)
    playlist._current_song = song
    return playlist


@pytest_asyncio.fixture
async def pl_prepare_media_none(mocker, pl):
    f = asyncio.Future()
    f.set_exception(MediaNotFound())
    mocker.patch.object(Playlist, '_prepare_media', side_effect=f)


@pytest_asyncio.fixture
async def pl_list_standby_return_empty(mocker, pl):
    f2 = asyncio.Future()
    f2.set_result([])
    mock_a_list_standby = pl._app.library.a_list_song_standby_v2
    mock_a_list_standby.return_value = f2


@pytest_asyncio.fixture
async def pl_list_standby_return_song2(mocker, pl, song2):
    f2 = asyncio.Future()
    f2.set_result([(song2, SONG2_URL)])
    mock_a_list_standby = pl._app.library.a_list_song_standby_v2
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
    pl._current_song = song
    pl.remove(song)
    assert len(pl) == 1
    assert pl.current_song == song1


@pytest.mark.asyncio
async def test_set_current_song_with_media(pl, song2):
    """
    Set a non-existing song as current song,
    and the song should be inserted after current_song.
    """
    # Mock the a_next coroutine to avoid resource leak::
    #   RuntimeWarning: coroutine 'Playlist.a_next' was never awaited
    pl.a_next = mock.MagicMock(return_value=asyncio.Future())
    pl.set_current_song_with_media(song2, None)
    assert pl.current_song == song2
    assert pl.list()[1] == song2


@pytest.mark.asyncio
async def test_play_model(pl, app_mock, song, mocker):
    f = asyncio.Future()
    f.set_result(None)
    app_mock.task_mgr.run_afn_preemptive.return_value = f
    await pl.a_play_model(song)
    # The player.resume method must be called.
    assert app_mock.player.resume.called


@pytest.mark.asyncio
async def test_play_a_brief_song_model(
        pl, app_mock, library, ekaf_song0, ekaf_brief_song0, mocker):
    app_mock.library = library
    pl.add(ekaf_brief_song0)
    mocker.patch.object(pl, 'a_set_current_song')
    await pl.a_play_model(ekaf_brief_song0)
    # The song should be upgraded to a normal model
    assert ekaf_brief_song0 not in pl.current_song
    # Should called with the upgraded song model
    app_mock.task_mgr.run_afn_preemptive.assert_called_once_with(
        pl.a_set_current_song, ekaf_song0, name='playlist.set_current_model')


def test_set_models(pl, song1, song2):
    # Set a nonexisting song as current song
    # The song should be inserted after current_song
    pl.set_models([song1, song2])
    assert pl.list()[1] == song2


@pytest.mark.asyncio
async def test_set_current_song_with_bad_song_1(
        mocker, song2, pl,
        pl_prepare_media_none,
        pl_list_standby_return_empty):
    mock_set_current_song_with_media = mocker.patch.object(
        Playlist, 'set_current_song_with_media')
    mock_mark_as_bad = mocker.patch.object(Playlist, 'mark_as_bad')
    await pl.a_set_current_song(song2)
    # A song that has no valid media should be marked as bad
    assert mock_mark_as_bad.called
    # Since there is no standby song, the media should be None
    mock_set_current_song_with_media.assert_called_once_with(song2, None, None)


@pytest.mark.asyncio
async def test_set_current_song_with_bad_song_2(
        mocker, song2, pl,
        pl_prepare_media_none,
        pl_list_standby_return_song2):
    mock_set_current_song_with_media = mocker.patch.object(
        Playlist, 'set_current_song_with_media')
    mock_mark_as_bad = mocker.patch.object(Playlist, 'mark_as_bad')
    sentinal = object()
    mocker.patch.object(MetadataAssembler, 'prepare_for_song', return_value=sentinal)
    await pl.a_set_current_song(song2)
    # A song that has no valid media should be marked as bad
    assert mock_mark_as_bad.called
    mock_set_current_song_with_media.assert_called_once_with(song2, SONG2_URL, sentinal)


@pytest.mark.asyncio
async def test_set_current_song_with_bad_song_3(
        mocker, song2, app_mock,
        pl_prepare_media_none, ):
    """song has mv and the mv has valid media, should use mv's media as the media"""
    media = object()
    metadata = object()

    mock_set_current_song_with_media = mocker.patch.object(
        Playlist, 'set_current_song_with_media')
    mock_prepare_mv_media = mocker.patch.object(Playlist, '_prepare_mv_media',
                                                return_value=media)
    mocker.patch.object(MetadataAssembler, 'prepare_for_song', return_value=metadata)

    app_mock.config.ENABLE_MV_AS_STANDBY = 1
    pl = Playlist(app_mock)
    await pl.a_set_current_song(song2)
    mock_prepare_mv_media.assert_called_once_with(song2)
    mock_set_current_song_with_media.assert_called_once_with(song2, media, metadata)


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
    mocker.patch.object(MetadataAssembler, 'prepare_for_song')
    await pl.a_set_current_song(song1)
    assert pl.list().index(song2) == 2


@pytest.fixture
def mock_a_set_cursong(mocker):
    mocker.patch.object(Playlist, 'a_set_current_song', new=mock.MagicMock)


@pytest.fixture
def mock_prepare_metadata(mocker):
    mocker.patch.object(MetadataAssembler, 'prepare_for_song', return_value=object())


@pytest.mark.asyncio
async def test_playlist_change_mode(app_mock, mocker):
    # from normal to fm
    pl = Playlist(app_mock)
    old_playback_mode = pl.playback_mode
    pl.mode = PlaylistMode.fm
    assert pl.playback_mode is PlaybackMode.sequential

    # from fm to normal
    pl.mode = PlaylistMode.normal
    assert pl.mode is PlaylistMode.normal
    assert pl.playback_mode == old_playback_mode


@pytest.mark.asyncio
async def test_playlist_change_repeat_shuffle_mode(app_mock):
    pl = Playlist(app_mock)
    pl.playback_mode = PlaybackMode.random
    assert pl.shuffle_mode is not PlaylistShuffleMode.off
    assert pl.repeat_mode is PlaylistRepeatMode.all

    pl.repeat_mode = PlaylistRepeatMode.none
    assert pl.shuffle_mode is PlaylistShuffleMode.off

    pl.shuffle_mode = PlaylistShuffleMode.songs
    assert pl.repeat_mode is PlaylistRepeatMode.all


@pytest.mark.asyncio
async def test_playlist_exit_fm_mode(app_mock, song, mock_prepare_metadata):
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    await pl.a_set_current_song(song)
    assert pl.mode is PlaylistMode.normal


@pytest.mark.asyncio
async def test_playlist_fm_mode_play_next(app_mock, song, song1, mock_prepare_metadata):
    pl = Playlist(app_mock)
    pl.mode = PlaylistMode.fm
    pl.fm_add(song1)
    pl.fm_add(song)
    pl._current_song = song1
    await pl.a_set_current_song(song)  # should not exit fm mode
    assert pl.mode is PlaylistMode.fm


@pytest.mark.asyncio
async def test_playlist_fm_mode_play_previous(app_mock, song, song1):
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
        pl._fm_add_no_lock(song)
        pl._next_no_lock()

    pl.eof_reached.connect(feed_playlist)
    pl.mode = PlaylistMode.fm
    pl.next()
    mock_set_current_song.assert_has_calls([mock.call(song)])


@pytest.mark.asyncio
async def test_playlist_remove_current_song(pl, song1, mocker):
    # Remove the current song, and it is the last song in the playlist.
    mock_emit = mocker.patch.object(pl.eof_reached, 'emit')
    pl.mode = PlaylistMode.fm
    pl._current_song = song1
    pl.remove(song1)
    assert mock_emit.called


@pytest.mark.asyncio
async def test_play_next_bad_song(app_mock, song, song1, mocker):
    """
    Prepare media for song raises unknown error, the song should
    be marked as bad. Besides, it should try to find standby.
    """
    mock_set_current_song_with_media = mocker.patch.object(
        Playlist, 'set_current_song_with_media')
    mocker.patch.object(MetadataAssembler, 'prepare_for_song', return_value=object())
    mock_standby = mocker.patch.object(Playlist,
                                       'find_and_use_standby',
                                       return_value=(song1, None))
    mocker.patch.object(Playlist, '_prepare_media', side_effect=Exception())
    mock_mark_as_bad = mocker.patch.object(Playlist, 'mark_as_bad')

    app_mock.config.ENABLE_MV_AS_STANDBY = 0
    pl = Playlist(app_mock)
    pl.add(song)
    pl.add(song1)
    pl._current_song = song
    await pl.a_set_current_song(pl.next_song)
    assert mock_mark_as_bad.called
    await asyncio.sleep(0.1)
    assert mock_set_current_song_with_media.called
    assert mock_standby.called


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
        pl.set_current_song(song1)
        pl.next()
        assert pl.current_song == song


def test_playlist_next_should_call_set_current_song(app_mock, mocker, song):
    mock_set_current_song = mocker.patch.object(Playlist, 'set_current_song')
    pl = Playlist(app_mock)
    pl.add(song)
    task = pl.next()
    # Next method should call set_current_song and return an asyncio task.
    # Since it is complex to mock and return a asyncio.Task, we do not
    # check the type of task object.
    assert task is not None
    assert mock_set_current_song.called


@pytest.mark.asyncio
async def test_playlist_prepare_metadata_for_song(
        app_mock, library, pl, ekaf_brief_song0, mocker):
    class Album:
        cover = 'http://'
        released = '2018-01-01'

    app_mock.library = library
    album = Album()
    mocker.patch.object(library, 'album_upgrade', return_value=album)
    # app_mock.library.album_upgrade.return_value = album
    # When cover is a media object, prepare_metadata should also succeed.
    await pl._metadata_mgr.prepare_for_song(ekaf_brief_song0)


def test_playlist_next_song(pl):
    pl.mark_as_bad(pl.list()[1])
    assert pl.next_song == pl.list()[0]
    pl.playback_mode = PlaybackMode.sequential
    assert pl.next_song is None
