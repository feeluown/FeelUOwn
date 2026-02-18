from typing import Any

from mcp.server.fastmcp import FastMCP
from feeluown.app import App, get_app
from feeluown.library import (
    ResolveFailed,
    ResolverNotFound,
    resolve,
    reverse,
    ModelType,
)
from feeluown.library.flags import Flags
from feeluown.library.provider_protocol import (
    SupportsCurrentUser,
    SupportsCurrentUserListPlaylists,
    SupportsCurrentUserListRadioSongs,
    SupportsRecListCollections,
    SupportsRecListDailyPlaylists,
    SupportsRecListDailySongs,
    SupportsToplist,
    SupportsPlaylistCreateByName,
    SupportsPlaylistDelete,
    SupportsPlaylistAddSong,
    SupportsPlaylistRemoveSong,
    SupportsSongLyric,
    SupportsSongWebUrl,
    SupportsVideoWebUrl,
)
from feeluown.serializers import serialize


mcp = FastMCP("FeelUOwn")
_PROTOCOLS = (
    SupportsCurrentUser,
    SupportsCurrentUserListPlaylists,
    SupportsCurrentUserListRadioSongs,
    SupportsRecListCollections,
    SupportsRecListDailyPlaylists,
    SupportsRecListDailySongs,
    SupportsToplist,
    SupportsPlaylistCreateByName,
    SupportsPlaylistDelete,
    SupportsPlaylistAddSong,
    SupportsPlaylistRemoveSong,
    SupportsSongLyric,
    SupportsSongWebUrl,
    SupportsVideoWebUrl,
)


def _require_app() -> App:
    app = get_app()
    if app is None:
        raise RuntimeError("app is not initialized")
    return app


def _player_nowplaying_metadata() -> dict[str, Any] | None:
    app = _require_app()
    return serialize("python", app.player.current_metadata)


def _playlist_list() -> list[dict[str, Any]]:
    app = _require_app()
    return serialize("python", app.playlist.list())


def _player_play_media_by_uri(uri: str) -> bool:
    app = _require_app()
    for model in app.playlist.list():
        if reverse(model) == uri:
            app.playlist.play_model(model)
            return True
    return False


def _current_song_uri() -> str | None:
    app = _require_app()
    song = app.playlist.current_song
    if song is None:
        return None
    return reverse(song)


def _provider_flags(provider) -> dict[str, list[str]]:
    flags_map: dict[str, list[str]] = {}
    meta_flags = getattr(provider.meta, "flags", {}) or {}
    for model_type, flags in meta_flags.items():
        if not isinstance(model_type, ModelType):
            continue
        if flags is None:
            continue
        names = [
            flag.name
            for flag in Flags
            if flag is not Flags.none and flag in flags
        ]
        if names:
            flags_map[model_type.name] = names
    return flags_map


def _provider_protocols(provider) -> list[str]:
    return [proto.__name__ for proto in _PROTOCOLS if isinstance(provider, proto)]


@mcp.tool()
def player_nowplaying_metadata() -> dict[str, Any] | None:
    """
    Get the metadata of the currently playing track.
    """
    return _player_nowplaying_metadata()


@mcp.resource("player://playlist")
def playlist_list() -> list[dict[str, Any]]:
    """
    List all tracks in the current playlist queue.
    Each item includes a `uri` field.
    """
    return _playlist_list()


@mcp.resource("player://nowplaying")
def nowplaying() -> dict[str, Any] | None:
    """
    Get the current playing track info.
    """
    metadata = _player_nowplaying_metadata()
    if metadata is None:
        return None
    return {
        "uri": _current_song_uri(),
        "metadata": metadata,
    }


@mcp.resource("library://providers")
def library_providers() -> list[dict[str, Any]]:
    app = _require_app()
    providers = []
    for provider in app.library.list():
        providers.append(
            {
                "id": provider.identifier,
                "name": provider.name,
            }
        )
    return providers


@mcp.tool()
def player_play_media_by_uri(uri: str) -> bool:
    """
    Play a track by URI if it exists in the current playlist queue.
    """
    return _player_play_media_by_uri(uri)


@mcp.tool()
def player_toggle() -> None:
    _require_app().player.toggle()


@mcp.tool()
def player_play() -> None:
    _require_app().player.resume()


@mcp.tool()
def player_pause() -> None:
    _require_app().player.pause()


@mcp.tool()
def player_seek(position: float) -> None:
    _require_app().player.position = position


@mcp.tool()
def player_status() -> dict[str, Any]:
    app = _require_app()
    player = app.player
    playlist = app.playlist
    return {
        "state": player.state.name,
        "position": player.position,
        "duration": player.duration,
        "volume": player.volume,
        "playback_mode": playlist.playback_mode.name,
        "nowplaying": nowplaying(),
    }


@mcp.tool()
def playlist_next() -> None:
    _require_app().playlist.next()


@mcp.tool()
def playlist_previous() -> None:
    _require_app().playlist.previous()


@mcp.tool()
def playlist_clear() -> None:
    _require_app().playlist.clear()


@mcp.tool()
def playlist_add_uri(uri: str) -> bool:
    app = _require_app()
    try:
        model = resolve(uri)
    except (ResolveFailed, ResolverNotFound):
        return False
    app.playlist.add(model)
    return True


@mcp.tool()
def playlist_play_uri(uri: str) -> bool:
    app = _require_app()
    try:
        model = resolve(uri)
    except (ResolveFailed, ResolverNotFound):
        return False
    app.playlist.add(model)
    app.playlist.play_model(model)
    return True


@mcp.tool()
def provider_capabilities(provider_id: str) -> dict[str, Any] | None:
    app = _require_app()
    provider = app.library.get(provider_id)
    if provider is None:
        return None
    return {
        "id": provider.identifier,
        "name": provider.name,
        "flags": _provider_flags(provider),
        "protocols": _provider_protocols(provider),
    }


def run_mcp_server(host: str = "127.0.0.1", port: int = 23335):
    """
    Run the MCP server in SSE mode.
    """
    mcp.settings.host = host
    mcp.settings.port = port
    return mcp.run_sse_async()
