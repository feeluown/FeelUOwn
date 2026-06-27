from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from feeluown.ai.radio import AIRadioSession
from feeluown.ai.radio import (
    ai_radio_activate,
    ai_radio_deactivate,
    ai_radio_get_state,
    ai_radio_update_preferences,
    fm_candidates_append,
    fm_candidates_clear,
    fm_candidates_keep,
    fm_candidates_remove,
    fm_candidates_replace,
)
from feeluown.player.fm_candidates import FMCandidateManager
from feeluown.player import Playlist, PlaylistMode
from feeluown.utils.dispatch import Signal


class FakeAI:
    def __init__(self):
        self.radio = None
        self._app = None

    def get_copilot(self):
        raise AssertionError("AI radio recommendation should not use Copilot")

    def get_active_radio(self):
        if self.radio is not None and self.radio.is_active:
            return self.radio
        return None

    def activate_radio(self, reset=True):
        radio = self.get_active_radio()
        if radio is not None:
            return radio
        radio = AIRadioSession(self._app)
        radio.activate(reset=reset)
        return radio

    def deactivate_radio(self):
        if self.radio is None:
            return False
        was_active = self.radio.is_active
        self.radio.deactivate()
        return was_active


class FakeFM:
    def __init__(self, app):
        self._app = app
        self.is_active = False
        self.fetch_songs_func = None
        self.reset = None
        self.candidates = FMCandidateManager(app)
        self.activate_count = 0

    def activate(self, fetch_songs_func, reset=True):
        self.is_active = True
        self.fetch_songs_func = fetch_songs_func
        self.reset = reset
        self.activate_count += 1
        self._app.playlist.mode = PlaylistMode.fm

    def deactivate(self):
        self.is_active = False
        self._app.playlist.mode = PlaylistMode.normal


class FakeRuntime:
    def __init__(self, app):
        self.context = SimpleNamespace(app=app)


class FakeRecommendationAgent:
    def __init__(self, suggestions):
        self.suggestions = suggestions
        self.calls = []

    async def ainvoke(self, input_, config, context):
        self.calls.append((input_, config, context))
        context.suggestions = self.suggestions


class FakeMatcher:
    songs_by_title = {}

    def __init__(self, _app):
        pass

    async def match(self, suggestion):
        return self.songs_by_title.get(suggestion.title)


def create_radio_app():
    app = SimpleNamespace()
    app.config = MagicMock()
    app.coll_mgr = MagicMock()
    app.player = SimpleNamespace(
        media_finished=Signal(),
        set_infinite_loop=lambda _enabled: None,
    )
    app.playlist = Playlist(app)
    app.playlist.mode = PlaylistMode.fm
    app.ai = FakeAI()
    app.ai._app = app
    app.fm = FakeFM(app)
    return app


def create_runtime_with_radio(song, *candidates, matcher_cls=None):
    app = create_radio_app()
    app.playlist.fm_add(song)
    for candidate in candidates:
        app.playlist.fm_add(candidate)
    app.playlist._current_song = song
    radio = AIRadioSession(app, matcher_cls=matcher_cls)
    radio.activate(reset=False)
    app.ai.radio = radio
    return FakeRuntime(app), radio


def create_recommendation_agent_factory(suggestions):
    agent = FakeRecommendationAgent(suggestions)

    def factory(_config):
        return agent

    return factory, agent


@pytest.mark.asyncio
async def test_ai_radio_fetch_matches_suggestions_with_radio_state(
    song, song1, song2
):
    suggestions = [
        SimpleNamespace(title="hello world"),
        SimpleNamespace(title="duplicate"),
        SimpleNamespace(title="missing"),
        SimpleNamespace(title="second"),
    ]
    recommendation_agent_factory, recommendation_agent = (
        create_recommendation_agent_factory(suggestions)
    )
    app = create_radio_app()
    app.playlist.fm_add(song1)
    app.playlist._current_song = song1
    FakeMatcher.songs_by_title = {
        "hello world": song,
        "duplicate": song1,
        "second": song2,
    }
    radio = AIRadioSession(
        app,
        matcher_cls=FakeMatcher,
        recommendation_agent_factory=recommendation_agent_factory,
    )
    radio.update_preferences(
        preferences=["more jazz"],
        avoidances=["too noisy"],
        reason="user feedback",
    )

    songs = await radio.a_fetch_songs_func(2)

    assert songs == [song, song2]
    input_, config, _context = recommendation_agent.calls[0]
    assert config["configurable"]["thread_id"] == "ai-radio-1"
    prompt = input_["messages"][2]["content"]
    assert "推荐2首适合继续播放的歌给用户" in prompt
    assert "'preferences': ['more jazz']" in prompt
    assert "'avoidances': ['too noisy']" in prompt
    assert "'preference_notes': ['user feedback']" in prompt
    assert f"'identifier': '{song1.identifier}'" in prompt


@pytest.mark.asyncio
async def test_ai_radio_fetch_recommends_songs_without_local_candidate_queue(song1):
    recommendation_agent_factory, recommendation_agent = (
        create_recommendation_agent_factory([SimpleNamespace(title="second")])
    )
    app = create_radio_app()
    FakeMatcher.songs_by_title = {"second": song1}
    radio = AIRadioSession(
        app,
        matcher_cls=FakeMatcher,
        recommendation_agent_factory=recommendation_agent_factory,
    )

    assert radio.get_state_for_ai()["candidates"] == []

    songs = await radio.a_fetch_songs_func(2)

    assert songs == [song1]
    assert len(recommendation_agent.calls) == 1
    prompt = recommendation_agent.calls[0][0]["messages"][2]["content"]
    assert "推荐2首适合继续播放的歌给用户" in prompt


@pytest.mark.asyncio
async def test_fm_candidates_append_tool_matches_suggestions_in_small_batch(
    song, song1, song2, song3
):
    app = create_radio_app()
    app.playlist.fm_add(song)
    app.playlist._current_song = song
    FakeMatcher.songs_by_title = {
        "hello world": song1,
        "second": song2,
        "third": song3,
    }
    radio = AIRadioSession(app, matcher_cls=FakeMatcher, candidate_batch_size=2)
    radio.activate(reset=False)
    app.ai.radio = radio
    statuses = []
    radio.status_changed.connect(statuses.append, weak=False)

    result = await fm_candidates_append.coroutine(
        songs=[
            SimpleNamespace(title="hello world"),
            SimpleNamespace(title="second"),
            SimpleNamespace(title="third"),
        ],
        runtime=FakeRuntime(app),
    )

    assert app.playlist.list() == [song, song1, song2]
    assert result is True
    assert statuses[-1] == "Radio candidates updated: 2 songs"


def test_ai_radio_tools_return_inactive_error():
    runtime = FakeRuntime(SimpleNamespace(ai=FakeAI()))

    result = ai_radio_get_state.func(runtime=runtime)

    assert result["ok"] is False
    assert result["error_code"] == "AI_RADIO_INACTIVE"
    assert result["active"] is False
    assert result["candidate_count"] == 0


def test_ai_radio_command_tools_return_false_when_unavailable():
    runtime = FakeRuntime(SimpleNamespace(ai=None))

    assert ai_radio_activate.func(runtime=runtime) is False
    assert ai_radio_deactivate.func(runtime=runtime) is False


def test_ai_radio_candidate_tools_return_false_when_inactive():
    runtime = FakeRuntime(SimpleNamespace(ai=FakeAI()))

    assert fm_candidates_clear.func(runtime=runtime) is False


def test_ai_radio_activate_tool_creates_active_session():
    app = create_radio_app()
    runtime = FakeRuntime(app)

    result = ai_radio_activate.func(runtime=runtime, reset=False)

    assert result is True
    assert app.ai.radio is not None
    assert app.ai.radio.is_active is True
    assert app.fm.is_active is True
    assert app.fm.reset is False
    assert app.playlist.mode is PlaylistMode.fm
    assert app.fm.fetch_songs_func == app.ai.radio.fetch_songs_func


def test_ai_radio_activate_tool_is_idempotent(song):
    app = create_radio_app()
    radio = AIRadioSession(app)
    radio.activate(reset=False)
    app.ai.radio = radio
    runtime = FakeRuntime(app)

    result = ai_radio_activate.func(runtime=runtime)

    assert result is True
    assert app.ai.radio is radio
    assert app.fm.activate_count == 1


def test_ai_radio_deactivate_tool_stops_active_session():
    app = create_radio_app()
    runtime = FakeRuntime(app)
    ai_radio_activate.func(runtime=runtime)

    result = ai_radio_deactivate.func(runtime=runtime)

    assert result is True
    assert app.ai.radio is None
    assert app.fm.is_active is False
    assert app.playlist.mode is PlaylistMode.normal


def test_ai_radio_deactivate_tool_is_idempotent():
    app = create_radio_app()
    runtime = FakeRuntime(app)

    result = ai_radio_deactivate.func(runtime=runtime)

    assert result is True


def test_ai_radio_tools_expose_state_and_update_preferences(song, song1):
    runtime, radio = create_runtime_with_radio(song, song1)

    pref_result = ai_radio_update_preferences.func(
        runtime=runtime,
        preferences=["more 90s classics"],
        avoidances=["too popular"],
        reason="user dislikes current candidates",
    )
    state = ai_radio_get_state.func(runtime=runtime)

    assert pref_result is True
    assert radio.preferences == ["more 90s classics"]
    assert radio.avoidances == ["too popular"]
    assert state["ok"] is True
    assert state["active"] is True
    assert state["candidates"][0]["position"] == 1
    assert state["candidates"][0]["identifier"] == song1.identifier
    assert state["candidates"][0]["uri"] == "fuo://fake/songs/1"
    assert state["preferences"] == ["more 90s classics"]


def test_fm_candidates_clear_tool(song, song1, song2):
    runtime, _radio = create_runtime_with_radio(song, song1, song2)

    result = fm_candidates_clear.func(runtime=runtime)

    assert result is True
    assert runtime.context.app.playlist.list() == [song]


def test_fm_candidates_remove_and_keep_tools_use_fm_candidates(song, song1, song2):
    runtime, _radio = create_runtime_with_radio(song, song1, song2)

    remove_result = fm_candidates_remove.func(positions=[1], runtime=runtime)
    keep_result = fm_candidates_keep.func(positions=[1], runtime=runtime)

    assert remove_result is True
    assert keep_result is True
    assert runtime.context.app.playlist.list() == [song, song2]


@pytest.mark.asyncio
async def test_fm_candidates_replace_tool_uses_fm_candidates(song, song1, song2):
    FakeMatcher.songs_by_title = {"second": song2}
    runtime, radio = create_runtime_with_radio(song, song1, matcher_cls=FakeMatcher)

    result = await fm_candidates_replace.coroutine(
        songs=[SimpleNamespace(title="second")],
        keep_positions=[],
        runtime=runtime,
    )

    assert result is True
    assert runtime.context.app.playlist.list() == [song, song2]
    assert radio.status == "Radio candidates updated: 1 songs"
