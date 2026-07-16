from types import SimpleNamespace
from unittest.mock import MagicMock

from feeluown.ai.copilot import (
    SongSuggestion,
    Copilot,
    tools,
)
from feeluown.ai.tools.suggestions import (
    create_song_suggestions_artifact,
    play_song_suggestion,
)
from feeluown.ai.tools.artifacts import play_library_search_result_song
from feeluown.library import BriefSongModel, SimpleSearchResult


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


def test_copilot_adds_search_result_artifact(mocker):
    app = SimpleNamespace(config=SimpleNamespace())
    mocker.patch("feeluown.ai.copilot.create_agent_with_config")
    copilot = Copilot(app)
    received = []
    copilot.artifact_added.connect(received.append, weak=False)
    song = BriefSongModel(
        source="fake",
        identifier="song-1",
        title="Song",
        artists_name="Mary",
    )
    search_result = SimpleSearchResult(
        q="Song",
        source="fake",
        songs=[song],
    )

    artifact = copilot.add_search_result_artifact(
        [search_result], title="Song"
    )

    assert artifact.identifier == 1
    assert artifact.type == "search_result"
    assert artifact.title == "Song"
    assert artifact.result == [search_result]
    assert artifact.songs == [song]
    assert copilot.get_artifact(1) is artifact
    assert copilot.get_artifact_song(1, 1) is song
    assert copilot.get_library_search_result_song(1, 1) is song
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

    result = play_song_suggestion.func(song=suggestion, runtime=runtime)

    playlist.play_model.assert_called_once()
    song = playlist.play_model.call_args.args[0]
    assert song.source == "ai"
    assert song.title == "hello world"
    assert song.artists_name == "mary"
    assert result["ok"] is True
    assert result["action"] == "play_song_suggestion"


def test_create_song_suggestions_artifact_normalizes_valid_songs(mocker):
    app = SimpleNamespace(config=SimpleNamespace())
    mocker.patch("feeluown.ai.copilot.create_agent_with_config")
    copilot = Copilot(app)
    runtime = SimpleNamespace(context=SimpleNamespace(copilot=copilot))

    result = create_song_suggestions_artifact.func(
        songs=[
            SongSuggestion(
                title=" hello world ",
                artists_name=" mary ",
                description=" nice ",
            ),
            SongSuggestion(title=" ", artists_name="nobody", description=""),
        ],
        runtime=runtime,
        title=" Picks ",
    )

    artifact = copilot.get_artifact(result["data"]["artifact_id"])
    assert result["ok"] is True
    assert artifact.title == "Picks"
    assert len(artifact.songs) == 1
    assert artifact.songs[0].title == "hello world"
    assert artifact.songs[0].artists_name == "mary"
    assert artifact.songs[0].description == "nice"


def test_create_song_suggestions_artifact_rejects_too_many_songs(mocker):
    app = SimpleNamespace(config=SimpleNamespace())
    mocker.patch("feeluown.ai.copilot.create_agent_with_config")
    copilot = Copilot(app)
    runtime = SimpleNamespace(context=SimpleNamespace(copilot=copilot))

    result = create_song_suggestions_artifact.func(
        songs=[
            SongSuggestion(title=f"Song {i}", artists_name="", description="")
            for i in range(21)
        ],
        runtime=runtime,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "TOO_MANY_SONG_SUGGESTIONS"
    assert result["data"]["max_song_count"] == 20
    assert copilot.get_artifacts() == []


def test_play_library_search_result_song_tool_plays_search_result_song(mocker):
    playlist = SimpleNamespace(play_model=MagicMock())
    app = SimpleNamespace(config=SimpleNamespace(), playlist=playlist)
    mocker.patch("feeluown.ai.copilot.create_agent_with_config")
    copilot = Copilot(app)
    song = BriefSongModel(
        source="fake",
        identifier="song-1",
        title="Song",
        artists_name="Mary",
    )
    copilot.add_search_result_artifact(
        [SimpleSearchResult(q="Song", source="fake", songs=[song])]
    )
    runtime = SimpleNamespace(context=SimpleNamespace(app=app, copilot=copilot))

    result = play_library_search_result_song.func(
        artifact_id=1,
        song_position=1,
        runtime=runtime,
    )

    playlist.play_model.assert_called_once_with(song)
    assert result["ok"] is True
    assert result["action"] == "play_library_search_result_song"
    assert result["data"]["song"]["identifier"] == "song-1"


def test_play_library_search_result_song_rejects_song_suggestion_artifact(mocker):
    playlist = SimpleNamespace(play_model=MagicMock())
    app = SimpleNamespace(config=SimpleNamespace(), playlist=playlist)
    mocker.patch("feeluown.ai.copilot.create_agent_with_config")
    copilot = Copilot(app)
    copilot.add_songs_artifact(
        [
            SongSuggestion(
                title="hello world",
                artists_name="mary",
                description="",
            )
        ]
    )
    runtime = SimpleNamespace(context=SimpleNamespace(app=app, copilot=copilot))

    result = play_library_search_result_song.func(
        artifact_id=1,
        song_position=1,
        runtime=runtime,
    )

    playlist.play_model.assert_not_called()
    assert result["ok"] is False
    assert result["error"]["code"] == "SEARCH_RESULT_SONG_NOT_FOUND"
    assert copilot.get_library_search_result_song(1, 1) is None


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


def test_copilot_exposes_library_tools():
    tool_names = {tool.name for tool in tools}

    assert "library_search" in tool_names
    assert "play_library_search_result_song" in tool_names


def test_copilot_does_not_expose_fuoexec_tool():
    tool_names = {tool.name for tool in tools}

    assert "fuoexec_execute" not in tool_names


def test_copilot_exposes_fm_candidate_tools():
    tool_names = {tool.name for tool in tools}

    assert {
        "fm_candidates_get_state",
        "fm_candidates_remove",
        "fm_candidates_append",
    }.issubset(tool_names)
    assert "fm_candidates_clear" not in tool_names
    assert "fm_candidates_keep" not in tool_names
    assert "fm_candidates_replace" not in tool_names
