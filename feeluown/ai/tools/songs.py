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
def play_song_by_uri(
    song_uri: str,
    runtime: ToolRuntime,
) -> dict:
    """Play a SongModel by URI.

    Use this when the user asks to play a real SongModel URI returned by
    library_search or another FeelUOwn tool.

    :param song_uri: SongModel URI.
    """
    try:
        song = runtime.context.copilot.get_song_by_uri(song_uri)
    except ValueError:
        return tool_error(
            "play_song_by_uri",
            "INVALID_SONG_URI",
            "A valid SongModel URI is required.",
            data={"song_uri": song_uri},
        )
    except Exception:  # noqa
        return tool_error(
            "play_song_by_uri",
            "SONG_MODEL_NOT_FOUND",
            "SongModel was not found for the given URI.",
            data={"song_uri": song_uri},
        )

    runtime.context.app.playlist.play_model(song)
    return tool_success(
        "play_song_by_uri",
        data={
            "song_uri": song_uri,
            "song": _song_to_ai_dict(song),
        },
    )


song_tools = [
    play_song_by_uri,
]
