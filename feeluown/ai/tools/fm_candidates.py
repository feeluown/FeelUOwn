from langchain.tools import tool, ToolRuntime

from feeluown.ai.tools.result import tool_bool_result, tool_error, tool_success
from feeluown.library import BriefSongModel
from feeluown.player.playlist import PlaylistMode
from feeluown.serializers import serialize


MAX_APPEND_SONGS = 3


def _get_fm_candidates(runtime: ToolRuntime):
    return runtime.context.app.fm.candidates


def _is_fm_active(runtime: ToolRuntime):
    return runtime.context.app.playlist.mode is PlaylistMode.fm


def _fm_candidate_result(action: str, success: bool, runtime: ToolRuntime):
    return tool_bool_result(
        action,
        success,
        "FM_INACTIVE",
        "FM mode is not active.",
        data={"active": _is_fm_active(runtime)},
    )


def _song_to_ai_dict(song: BriefSongModel, position: int | None = None):
    data = serialize("python", song)
    data["source"] = data.pop("provider", data.get("source"))
    data.pop("__type__", None)
    if position is not None:
        data["position"] = position
    return data


@tool
def fm_candidates_get_state(runtime: ToolRuntime) -> dict:
    """Get current FM candidate state and upcoming candidate songs."""
    fm_candidates = _get_fm_candidates(runtime)
    candidates = fm_candidates.list_candidates()
    return tool_success(
        "fm_candidates_get_state",
        data={
            "active": _is_fm_active(runtime),
            "candidates": [
                _song_to_ai_dict(song, position)
                for position, song in enumerate(candidates, start=1)
            ],
            "candidate_count": len(candidates),
        },
    )


@tool
def fm_candidates_remove(positions: list[int], runtime: ToolRuntime) -> dict:
    """Remove upcoming FM candidate songs by 1-based positions.

    :param positions: 1-based candidate positions to remove.
    """
    fm_candidates = _get_fm_candidates(runtime)
    return _fm_candidate_result(
        "fm_candidates_remove",
        fm_candidates.remove(positions),
        runtime,
    )


@tool
def fm_candidates_append(
    song_uris: list[str], runtime: ToolRuntime
) -> dict:
    """Append songs to the FM candidate list by SongModel URI.

    FM candidates are SongModel items. Use library_search first when you need
    to discover SongModel URIs from text.

    Append at most 3 songs in one call. When adding more songs, split the work
    into smaller batches so matching/searching remains observable and bounded.

    :param song_uris: SongModel URI list to append.
    """
    if len(song_uris) > MAX_APPEND_SONGS:
        return tool_error(
            "fm_candidates_append",
            "TOO_MANY_SONGS",
            "Append at most 3 songs in one fm_candidates_append call.",
            data={
                "success": False,
                "max_song_count": MAX_APPEND_SONGS,
                "song_count": len(song_uris),
                "active": _is_fm_active(runtime),
            },
        )
    if not _is_fm_active(runtime):
        return _fm_candidate_result("fm_candidates_append", False, runtime)

    songs = []
    for uri in song_uris:
        try:
            song = runtime.context.copilot.get_song_by_uri(uri)
        except ValueError:
            return tool_error(
                "fm_candidates_append",
                "INVALID_SONG_URI",
                "A valid SongModel URI is required.",
                data={
                    "success": False,
                    "song_uri": uri,
                    "active": _is_fm_active(runtime),
                },
            )
        except Exception:  # noqa
            return tool_error(
                "fm_candidates_append",
                "SONG_MODEL_NOT_FOUND",
                "SongModel was not found for the given URI.",
                data={
                    "success": False,
                    "song_uri": uri,
                    "active": _is_fm_active(runtime),
                },
            )
        songs.append(song)
    fm_candidates = _get_fm_candidates(runtime)
    return _fm_candidate_result(
        "fm_candidates_append",
        fm_candidates.append(songs),
        runtime,
    )


fm_candidates_tools = [
    fm_candidates_get_state,
    fm_candidates_remove,
    fm_candidates_append,
]
