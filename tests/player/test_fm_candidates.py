from unittest.mock import MagicMock

from feeluown.player import Playlist, PlaylistMode
from feeluown.player.fm_candidates import FMCandidateManager


def create_candidate_manager():
    app = MagicMock()
    app.playlist = Playlist(app)
    app.playlist.mode = PlaylistMode.fm
    return app, FMCandidateManager(app)


def test_fm_candidates_remove_and_keep_upcoming_songs(song, song1, song2, song3):
    app, candidates = create_candidate_manager()
    app.playlist.fm_add(song)
    app.playlist.fm_add(song1)
    app.playlist.fm_add(song2)
    app.playlist.fm_add(song3)
    app.playlist._current_song = song

    ok = candidates.remove([2])

    assert ok is True
    assert app.playlist.list() == [song, song1, song3]

    ok = candidates.keep([2])

    assert ok is True
    assert app.playlist.list() == [song, song3]


def test_fm_candidates_clear_and_append(song, song1, song2):
    app, candidates = create_candidate_manager()
    app.playlist.fm_add(song)
    app.playlist.fm_add(song1)
    app.playlist._current_song = song

    ok = candidates.clear()

    assert ok is True
    assert app.playlist.list() == [song]

    ok = candidates.append([song2])

    assert ok is True
    assert candidates.list_candidates() == [song2]
    assert app.playlist.list() == [song, song2]


def test_fm_candidates_replace_keeps_selected_positions(song, song1, song2, song3):
    app, candidates = create_candidate_manager()
    app.playlist.fm_add(song)
    app.playlist.fm_add(song1)
    app.playlist.fm_add(song2)
    app.playlist._current_song = song

    ok = candidates.replace([song3], keep_positions=[2])

    assert ok is True
    assert candidates.list_candidates() == [song2, song3]
    assert app.playlist.list() == [song, song2, song3]


def test_fm_candidates_reject_operations_outside_fm(song):
    app = MagicMock()
    app.playlist = Playlist(app)
    app.playlist.add(song)
    candidates = FMCandidateManager(app)

    ok = candidates.clear()

    assert ok is False
    assert app.playlist.list() == [song]
