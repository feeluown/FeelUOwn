from langchain.tools import tool, ToolRuntime

from feeluown.ai.models import SongSuggestion
from feeluown.ai.tools.result import tool_error, tool_success
from feeluown.library import BriefSongModel
from feeluown.serializers import serialize


def _song_to_ai_dict(song: BriefSongModel):
    data = serialize("python", song)
    data["source"] = data.pop("provider", data.get("source"))
    data.pop("__type__", None)
    return data


def _to_playable_song(song: SongSuggestion | BriefSongModel):
    if isinstance(song, SongSuggestion):
        return song.to_brief_song()
    return song


@tool
def play_artifact_song(
    artifact_id: int,
    song_position: int,
    runtime: ToolRuntime,
) -> dict:
    """Play a song from a Copilot artifact by 1-based song position.

    Use this after library_search returns an artifact_id and the user asks to
    play one of the songs in that artifact.

    :param artifact_id: Artifact identifier returned by a tool.
    :param song_position: 1-based song position in the artifact song list.
    """
    song = runtime.context.copilot.get_artifact_song(artifact_id, song_position)
    if song is None:
        return tool_error(
            "play_artifact_song",
            "ARTIFACT_SONG_NOT_FOUND",
            "Artifact song was not found.",
            data={
                "artifact_id": artifact_id,
                "song_position": song_position,
            },
        )

    playable_song = _to_playable_song(song)
    runtime.context.app.playlist.play_model(playable_song)
    return tool_success(
        "play_artifact_song",
        data={
            "artifact_id": artifact_id,
            "song_position": song_position,
            "song": _song_to_ai_dict(playable_song),
        },
    )


artifact_tools = [
    play_artifact_song,
]
