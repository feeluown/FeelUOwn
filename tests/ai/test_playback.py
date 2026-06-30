from types import SimpleNamespace
from unittest.mock import MagicMock

from feeluown.ai.playback import (
    playback_adjust_volume,
    playback_get_state,
    playback_next_track,
    playback_pause,
    playback_previous_track,
    playback_resume,
    playback_set_volume,
    playback_stop,
    playback_toggle,
)
from feeluown.library import BriefSongModel
from feeluown.player import State


class FakeRuntime:
    def __init__(self, app):
        self.context = SimpleNamespace(app=app)


class FakePlayer:
    def __init__(self):
        self.state = State.paused
        self.position = 12
        self.duration = 120
        self._volume = 50
        self.pause = MagicMock()
        self.resume = MagicMock()
        self.toggle = MagicMock()
        self.stop = MagicMock()

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value


def create_runtime(song=None):
    app = SimpleNamespace(
        player=FakePlayer(),
        playlist=SimpleNamespace(
            current_song=song,
            next=MagicMock(),
            previous=MagicMock(),
        ),
    )
    return FakeRuntime(app)


def test_playback_get_state_exposes_current_playback_state():
    song = BriefSongModel(
        source="fake",
        identifier="1",
        title="hello world",
        artists_name="mary",
    )
    runtime = create_runtime(song)

    result = playback_get_state.func(runtime=runtime)

    assert result["ok"] is True
    assert result["action"] == "get_state"
    assert result["player_state"] == "paused"
    assert result["volume"] == 50
    assert result["position"] == 12
    assert result["duration"] == 120
    assert result["current_song"]["source"] == "fake"
    assert result["current_song"]["identifier"] == "1"


def test_playback_track_navigation_uses_playlist():
    runtime = create_runtime()

    next_result = playback_next_track.func(runtime=runtime)
    previous_result = playback_previous_track.func(runtime=runtime)

    runtime.context.app.playlist.next.assert_called_once()
    runtime.context.app.playlist.previous.assert_called_once()
    assert next_result["action"] == "next_track"
    assert previous_result["action"] == "previous_track"


def test_playback_player_controls_use_player():
    runtime = create_runtime()

    pause_result = playback_pause.func(runtime=runtime)
    resume_result = playback_resume.func(runtime=runtime)
    toggle_result = playback_toggle.func(runtime=runtime)
    stop_result = playback_stop.func(runtime=runtime)

    player = runtime.context.app.player
    player.pause.assert_called_once()
    player.resume.assert_called_once()
    player.toggle.assert_called_once()
    player.stop.assert_called_once()
    assert pause_result["action"] == "pause"
    assert resume_result["action"] == "resume"
    assert toggle_result["action"] == "toggle"
    assert stop_result["action"] == "stop"


def test_playback_volume_tools_clamp_values():
    runtime = create_runtime()

    too_high = playback_set_volume.func(volume=120, runtime=runtime)
    down = playback_adjust_volume.func(delta=-130, runtime=runtime)
    up = playback_adjust_volume.func(delta=20, runtime=runtime)

    assert too_high["volume"] == 100
    assert down["volume"] == 0
    assert up["volume"] == 20
