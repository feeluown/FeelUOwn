from langchain.tools import tool, ToolRuntime

from feeluown.ai.models import SongSuggestion
from feeluown.ai.tools.result import tool_error, tool_success


MAX_SONG_SUGGESTIONS_PER_ARTIFACT = 20


def _normalize_song_suggestion(song: SongSuggestion) -> SongSuggestion | None:
    title = song.title.strip()
    artists_name = song.artists_name.strip()
    description = song.description.strip()
    if not title:
        return None
    return SongSuggestion(
        title=title,
        artists_name=artists_name,
        description=description,
    )


@tool
def play_song_suggestion(
    song: SongSuggestion,
    runtime: ToolRuntime,
) -> dict:
    """Play a song suggestion.

    Use this only when the latest user message explicitly asks to play one
    specific suggested song. Do not use it to auto-play a list of recommended
    songs; create an artifact instead.

    :param song: A SongSuggestion.
    """
    normalized_song = _normalize_song_suggestion(song)
    if normalized_song is None:
        return tool_error(
            "play_song_suggestion",
            "INVALID_SONG_SUGGESTION",
            "SongSuggestion title is required.",
        )
    runtime.context.app.playlist.play_model(normalized_song.to_brief_song())
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
    normalized_songs = [
        song for song in (_normalize_song_suggestion(song) for song in songs)
        if song is not None
    ]
    if not normalized_songs:
        return tool_error(
            "create_song_suggestions_artifact",
            "NO_VALID_SONG_SUGGESTIONS",
            "At least one SongSuggestion with a title is required.",
        )
    if len(normalized_songs) > MAX_SONG_SUGGESTIONS_PER_ARTIFACT:
        return tool_error(
            "create_song_suggestions_artifact",
            "TOO_MANY_SONG_SUGGESTIONS",
            (
                "Too many song suggestions. Create a smaller artifact instead."
            ),
            data={
                "max_song_count": MAX_SONG_SUGGESTIONS_PER_ARTIFACT,
                "song_count": len(normalized_songs),
            },
        )
    artifact = runtime.context.copilot.add_songs_artifact(
        normalized_songs, title=title.strip()
    )
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
