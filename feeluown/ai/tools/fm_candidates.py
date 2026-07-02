from langchain.tools import tool, ToolRuntime

from feeluown.ai.tools.result import tool_bool_result, tool_success
from feeluown.library import BriefSongModel
from feeluown.player.playlist import PlaylistMode
from feeluown.serializers import serialize


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
    songs: list[BriefSongModel], runtime: ToolRuntime
) -> dict:
    """Append real songs to the FM candidate list.

    FM candidates are real provider songs. Use library_search first when you
    need to discover real provider songs from text.

    :param songs: Real provider songs to append.
    """
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
