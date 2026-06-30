from types import SimpleNamespace
from unittest.mock import MagicMock

from feeluown.ai.copilot import (
    SongSuggestion,
    Copilot,
    play_song_suggestion,
    tools,
)


def test_copilot_adds_song_artifact_without_mutating_playlist(mocker):
    app = SimpleNamespace(config=SimpleNamespace())
    mocker.patch("feeluown.ai.copilot.create_agent_with_config")
    copilot = Copilot(app)
    received = []
    copilot.artifact_added.connect(received.append, weak=False)
    songs = [
        SongSuggestion(
            title="hello world",
            artists_name="mary",
            description="",
        )
    ]

    artifact = copilot.add_songs_artifact(songs, title="Night Songs")

    assert artifact.identifier == 1
    assert artifact.type == "songs"
    assert artifact.title == "Night Songs"
    assert artifact.songs == songs
    assert copilot.get_artifacts() == [artifact]
    assert received == [artifact]


def test_play_song_suggestion_tool_plays_song_suggestion():
    playlist = SimpleNamespace(play_model=MagicMock())
    runtime = SimpleNamespace(
        context=SimpleNamespace(app=SimpleNamespace(playlist=playlist))
    )
    suggestion = SongSuggestion(
        title="hello world",
        artists_name="mary",
        description="",
    )

    play_song_suggestion.func(song=suggestion, runtime=runtime)

    playlist.play_model.assert_called_once()
    song = playlist.play_model.call_args.args[0]
    assert song.source == "ai"
    assert song.title == "hello world"
    assert song.artists_name == "mary"


def test_copilot_tool_names_are_specific_to_song_suggestions():
    tool_names = {tool.name for tool in tools}

    assert "play_song_suggestion" in tool_names
    assert "play_song" not in tool_names


def test_copilot_exposes_playback_tools():
    tool_names = {tool.name for tool in tools}

    assert {
        "playback_get_state",
        "playback_next_track",
        "playback_previous_track",
        "playback_pause",
        "playback_resume",
        "playback_toggle",
        "playback_stop",
        "playback_set_volume",
        "playback_adjust_volume",
    }.issubset(tool_names)
