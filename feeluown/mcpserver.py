from typing import Any

from mcp.server.fastmcp import FastMCP
from feeluown.app import App, get_app
from feeluown.library import reverse
from feeluown.serializers import serialize


mcp = FastMCP("FeelUOwn")


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
def playlist_next() -> None:
    _require_app().playlist.next()


@mcp.tool()
def playlist_previous() -> None:
    _require_app().playlist.previous()


def run_mcp_server(host: str = "127.0.0.1", port: int = 23335):
    """
    Run the MCP server in SSE mode.
    """
    mcp.settings.host = host
    mcp.settings.port = port
    return mcp.run_sse_async()
