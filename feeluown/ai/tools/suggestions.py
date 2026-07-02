from langchain.tools import tool, ToolRuntime

from feeluown.ai.models import SongSuggestion
from feeluown.ai.tools.result import tool_success


@tool
def play_song_suggestion(song: SongSuggestion, runtime: ToolRuntime) -> dict:
    """Play a song suggestion.

    :param song: A SongSuggestion.
    """
    runtime.context.app.playlist.play_model(song.to_brief_song())
    return tool_success("play_song_suggestion")


@tool
def create_song_suggestions_artifact(
    songs: list[SongSuggestion],
    runtime: ToolRuntime,
    title: str = "",
) -> dict:
    """Create an interactive artifact for song suggestions.

    Use this when you recommend multiple songs and want the user to inspect them
    in the AI assistant UI.

    :param songs: A list of SongSuggestion.
    :param title: Optional artifact title.
    """
    artifact = runtime.context.copilot.add_songs_artifact(songs, title=title)
    return tool_success(
        "create_song_suggestions_artifact",
        data={
            "artifact_id": artifact.identifier,
            "title": artifact.title,
            "song_count": len(artifact.songs),
        },
    )


suggestion_tools = [
    play_song_suggestion,
    create_song_suggestions_artifact,
]
