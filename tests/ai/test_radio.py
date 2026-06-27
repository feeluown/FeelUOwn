from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from feeluown.ai.radio import AIRadioSession
from feeluown.player import Playlist, PlaylistMode


class FakeCopilot:
    def __init__(self, suggestions):
        self.suggestions = suggestions
        self.calls = []

    async def recommend_songs(self, number, instructions=None):
        self.calls.append((number, instructions))
        return self.suggestions


class FakeAI:
    def __init__(self, copilot):
        self._copilot = copilot
        self.radio = None

    def get_copilot(self):
        return self._copilot


class FakeMatcher:
    songs_by_title = {}

    def __init__(self, _app):
        pass

    async def match(self, suggestion):
        return self.songs_by_title.get(suggestion.title)


@pytest.mark.asyncio
async def test_ai_radio_fetch_matches_suggestions(song, song1, song2):
    suggestions = [
        SimpleNamespace(title="hello world"),
        SimpleNamespace(title="duplicate"),
        SimpleNamespace(title="missing"),
        SimpleNamespace(title="second"),
    ]
    copilot = FakeCopilot(suggestions)
    app = MagicMock()
    app.ai = FakeAI(copilot)
    app.playlist.list.return_value = [song1]
    FakeMatcher.songs_by_title = {
        "hello world": song,
        "duplicate": song1,
        "second": song2,
    }

    radio = AIRadioSession(app, matcher_cls=FakeMatcher)
    radio.add_instruction("more jazz")

    songs = await radio.a_fetch_songs_func(2)

    assert songs == [song, song2]
    assert copilot.calls == [(2, ["more jazz"])]


@pytest.mark.asyncio
async def test_ai_radio_uses_initial_songs_before_recommending(song, song1):
    copilot = FakeCopilot([SimpleNamespace(title="second")])
    app = MagicMock()
    app.ai = FakeAI(copilot)
    app.playlist.list.return_value = []
    FakeMatcher.songs_by_title = {"second": song1}

    radio = AIRadioSession(app, initial_songs=[song], matcher_cls=FakeMatcher)

    songs = await radio.a_fetch_songs_func(2)

    assert songs == [song, song1]
    assert copilot.calls == [(1, [])]


@pytest.mark.asyncio
async def test_ai_radio_updates_upcoming_candidates_in_playlist(song, song1, song2):
    suggestions = [
        SimpleNamespace(title="hello world"),
        SimpleNamespace(title="second"),
    ]
    copilot = FakeCopilot(suggestions)
    app = MagicMock()
    app.playlist = Playlist(app)
    app.playlist.mode = PlaylistMode.fm
    app.playlist.fm_add(song)
    app.playlist.fm_add(song1)
    app.playlist._current_song = song
    app.ai = FakeAI(copilot)
    FakeMatcher.songs_by_title = {
        "hello world": song1,
        "second": song2,
    }
    radio = AIRadioSession(app, matcher_cls=FakeMatcher)
    statuses = []
    radio.status_changed.connect(statuses.append, weak=False)

    result = await radio.update_candidates("换一批", count=2)

    assert app.playlist.list() == [song, song1, song2]
    assert result.removed_count == 1
    assert result.added_songs == [song1, song2]
    assert copilot.calls == [(2, ["换一批"])]
    assert statuses[-1] == "AI Radio candidates updated: 2 songs"


@pytest.mark.asyncio
async def test_ai_radio_keeps_some_candidates_before_refill(
    song, song1, song2, song3
):
    suggestions = [SimpleNamespace(title="third"), SimpleNamespace(title="missing")]
    copilot = FakeCopilot(suggestions)
    app = MagicMock()
    app.playlist = Playlist(app)
    app.playlist.mode = PlaylistMode.fm
    app.playlist.fm_add(song)
    app.playlist.fm_add(song1)
    app.playlist.fm_add(song2)
    app.playlist._current_song = song
    app.ai = FakeAI(copilot)
    FakeMatcher.songs_by_title = {"third": song3}
    radio = AIRadioSession(app, matcher_cls=FakeMatcher)

    result = await radio.update_candidates("保留前 1 首，补新的", count=2)

    assert app.playlist.list() == [song, song1, song3]
    assert result.kept_count == 1
    assert result.removed_count == 1
    assert result.requested_count == 1
    assert result.added_songs == [song3]
    assert copilot.calls == [(1, ["保留前 1 首，补新的"])]


@pytest.mark.asyncio
async def test_ai_radio_can_clear_upcoming_candidates(song, song1, song2):
    copilot = FakeCopilot([SimpleNamespace(title="unused")])
    app = MagicMock()
    app.playlist = Playlist(app)
    app.playlist.mode = PlaylistMode.fm
    app.playlist.fm_add(song)
    app.playlist.fm_add(song1)
    app.playlist.fm_add(song2)
    app.playlist._current_song = song
    app.ai = FakeAI(copilot)
    radio = AIRadioSession(app, matcher_cls=FakeMatcher)

    result = await radio.update_candidates("清空候选列表", count=2)

    assert app.playlist.list() == [song]
    assert result.removed_count == 2
    assert result.requested_count == 0
    assert result.added_songs == []
    assert copilot.calls == []
