from types import SimpleNamespace

from feeluown.ai.copilot import SongSuggestion, Copilot


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
