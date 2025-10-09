from typing import Optional, List

from mcp.server.fastmcp import FastMCP

from feeluown.app import get_app
from feeluown.library import reverse
from feeluown.serializers import serialize


mcp = FastMCP("FeelUOwn")


@mcp.tool()
def player_nowplaying_metadata() -> Optional[dict]:
    """
    Get the metadata of the current playing song of the player.
    For example, you can get the title/artist/album/uri of the song.
    """
    app = get_app()
    return serialize('python', app.player.current_metadata)


@mcp.resource("player://playlist")
def playlist_list() -> List[dict]:
    """
    Get all the songs in the playlist queue.
    Each song is indentified by the `uri` field.
    """
    app = get_app()
    return serialize('python', app.playlist.list())


@mcp.tool()
def player_play_media_by_uri(uri: str) -> bool:
    """
    Play a song by its uri.
    Return True if the song is played successfully.
    """
    app = get_app()
    for model in app.playlist.list():
        if reverse(model) == uri:
            app.playlist.play_model(model)
            return True
    return False


async def run_mcp_server(host='127.0.0.1', port=23335):
    """
    Run the MCP server.
    """
    mcp.settings.host = host
    mcp.settings.port = port

    app = get_app()
    mcp.add_tool(
        app.player.toggle,
        'player_toggle',
        'Toggle the player',
    )
    mcp.add_tool(
        app.playlist.next,
        'playlist_next',
        'Switch to the next media in the playlist',
    )
    mcp.add_tool(
        app.playlist.previous,
        'playlist_previous',
        'Switch to the previous media in the playlist',
    )

    await mcp.run_sse_async()
