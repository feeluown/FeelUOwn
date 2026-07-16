from langchain.tools import tool, ToolRuntime

from feeluown.ai.tools.result import tool_error, tool_success
from feeluown.library import BriefSongModel
from feeluown.serializers import serialize


def _song_to_ai_dict(song: BriefSongModel):
    data = serialize("python", song)
    data["source"] = data.pop("provider", data.get("source"))
    data.pop("__type__", None)
    return data


@tool
def play_library_search_result_song(
    artifact_id: int,
    song_position: int,
    runtime: ToolRuntime,
) -> dict:
    """Play a SongModel from a library_search result artifact.

    Use this after library_search returns an artifact_id and the user asks to
    play one of the SongModel items in that search result artifact.

    :param artifact_id: Artifact identifier returned by a tool.
    :param song_position: 1-based song position in the artifact song list.
    """
    song = runtime.context.copilot.get_library_search_result_song(
        artifact_id,
        song_position,
    )
    if song is None:
        return tool_error(
            "play_library_search_result_song",
            "SEARCH_RESULT_SONG_NOT_FOUND",
            (
                "Search result SongModel was not found. Use this tool only "
                "with library_search result artifacts."
            ),
            data={
                "artifact_id": artifact_id,
                "song_position": song_position,
            },
        )

    runtime.context.app.playlist.play_model(song)
    return tool_success(
        "play_library_search_result_song",
        data={
            "artifact_id": artifact_id,
            "song_position": song_position,
            "song": _song_to_ai_dict(song),
        },
    )


artifact_tools = [
    play_library_search_result_song,
]
