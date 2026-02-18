from typing import Any

from feeluown.app import App, get_app
from feeluown.library import reverse
from feeluown.serializers import serialize


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


def _build_mcp_server(host: str, port: int):
    # Import lazily so the module can be imported without the optional
    # `mcpserver` extra installed (e.g. in default test environments).
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("FeelUOwn")
    mcp.settings.host = host
    mcp.settings.port = port

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

    app = _require_app()
    mcp.add_tool(app.player.toggle, "player_toggle", "Toggle the player")
    mcp.add_tool(
        app.playlist.next,
        "playlist_next",
        "Switch to the next media in the playlist",
    )
    mcp.add_tool(
        app.playlist.previous,
        "playlist_previous",
        "Switch to the previous media in the playlist",
    )
    return mcp


def run_mcp_server(host: str = "127.0.0.1", port: int = 23335):
    """
    Create and run the MCP server in SSE mode.
    """
    mcp = _build_mcp_server(host, port)
    return mcp.run_sse_async()
