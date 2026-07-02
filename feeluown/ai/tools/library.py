import logging
import math
from typing import Any

from langchain.tools import tool, ToolRuntime

from feeluown.library import BaseModel, ModelType, SimpleSearchResult, reverse
from feeluown.ai.tools.result import tool_error, tool_success
from feeluown.serializers import serialize


logger = logging.getLogger(__name__)


DEFAULT_SEARCH_TIMEOUT = 8.0
MAX_SEARCH_TIMEOUT = 30.0
MIN_SEARCH_TIMEOUT = 0.5


def _normalize_ai_data(value: Any):
    if isinstance(value, dict):
        data = {}
        for key, item in value.items():
            if key == "__type__":
                continue
            normalized_key = "source" if key == "provider" else key
            data[normalized_key] = _normalize_ai_data(item)
        return data
    if isinstance(value, list):
        return [_normalize_ai_data(item) for item in value]
    return value


def _model_to_ai_dict(model: BaseModel | None, position: int | None = None):
    if model is None:
        return None
    data = _normalize_ai_data(serialize("python", model))
    data["model_type"] = ModelType(model.meta.model_type).name
    data["uri"] = reverse(model)
    if position is not None:
        data["position"] = position
    return data


def _models_to_ai_list(models, limit: int):
    return [
        _model_to_ai_dict(model, position)
        for position, model in enumerate(list(models)[:limit], start=1)
    ]


def _songs_to_ai_list(songs, limit: int, artifact_position_start: int):
    data = []
    for offset, song in enumerate(list(songs)[:limit], start=0):
        song_data = _model_to_ai_dict(song, offset + 1)
        song_data["artifact_song_position"] = artifact_position_start + offset
        data.append(song_data)
    return data


def _clamp_limit(limit: int, max_limit: int = 20):
    return max(1, min(int(limit), max_limit))


def _normalize_timeout(timeout: float | None):
    if timeout is None:
        return DEFAULT_SEARCH_TIMEOUT
    value = float(timeout)
    if not math.isfinite(value):
        return DEFAULT_SEARCH_TIMEOUT
    return max(MIN_SEARCH_TIMEOUT, min(value, MAX_SEARCH_TIMEOUT))


def _normalize_source_in(source_in):
    if source_in is None:
        return None
    if isinstance(source_in, str):
        return [source.strip() for source in source_in.split(",") if source.strip()]
    return list(source_in)


def _error_result(action: str, error: Exception):
    logger.debug("AI library tool failed: %s", action, exc_info=True)
    return tool_error(action, type(error).__name__, str(error))


def _search_result_to_ai_dict(
    result,
    limit: int,
    artifact_song_position_start: int = 1,
):
    return {
        "source": result.source,
        "query": result.q,
        "error_message": result.err_msg,
        "songs": _songs_to_ai_list(
            result.songs, limit, artifact_song_position_start
        ),
        "albums": _models_to_ai_list(result.albums, limit),
        "artists": _models_to_ai_list(result.artists, limit),
        "videos": _models_to_ai_list(result.videos, limit),
        "playlists": _models_to_ai_list(result.playlists, limit),
    }


def _limit_search_result(result, limit: int):
    return SimpleSearchResult(
        q=result.q,
        source=result.source,
        err_msg=result.err_msg,
        songs=list(result.songs)[:limit],
        albums=list(result.albums)[:limit],
        artists=list(result.artists)[:limit],
        videos=list(result.videos)[:limit],
        playlists=list(result.playlists)[:limit],
    )


@tool
async def library_search(
    keyword: str,
    runtime: ToolRuntime,
    type_in: str = "",
    source_in: list[str] | None = None,
    limit_per_type: int = 5,
    timeout: float | None = DEFAULT_SEARCH_TIMEOUT,
) -> dict:
    """Search online music providers for songs, artists, albums, videos, or playlists.

    :param keyword: Search keyword.
    :param type_in: Optional comma-separated types: song, artist, album, video, playlist.
    :param source_in: Optional provider identifiers to search in.
    :param limit_per_type: Maximum items per result type per provider, from 1 to 20.
    :param timeout: Maximum search time in seconds, clamped from 0.5 to 30.
    """
    action = "search"
    try:
        limit = _clamp_limit(limit_per_type)
        search_timeout = _normalize_timeout(timeout)
        sources = _normalize_source_in(source_in)
        results = []
        async for result in runtime.context.app.library.a_search(
            keyword,
            type_in=type_in or None,
            source_in=sources,
            timeout=search_timeout,
            return_err=True,
        ):
            if result is not None:
                results.append(_limit_search_result(result, limit))
        artifact = runtime.context.copilot.add_search_result_artifact(
            results,
            title=keyword,
        )
        result_dicts = []
        artifact_song_position = 1
        for result in results:
            result_dicts.append(
                _search_result_to_ai_dict(
                    result,
                    limit,
                    artifact_song_position,
                )
            )
            artifact_song_position += len(result.songs)
        return tool_success(
            action,
            data={
                "keyword": keyword,
                "type_in": type_in,
                "source_in": sources or [],
                "timeout": search_timeout,
                "artifact_id": artifact.identifier,
                "results": result_dicts,
            },
        )
    except Exception as e:  # noqa
        return _error_result(action, e)


library_tools = [library_search]
