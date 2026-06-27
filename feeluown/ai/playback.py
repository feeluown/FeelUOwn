from langchain.tools import tool, ToolRuntime

from feeluown.library import BriefSongModel
from feeluown.serializers import serialize


def _clamp_volume(volume: int) -> int:
    return max(0, min(100, int(volume)))


def _song_to_ai_dict(song: BriefSongModel | None):
    if song is None:
        return None
    data = serialize("python", song)
    data["source"] = data.pop("provider", data.get("source"))
    data.pop("__type__", None)
    return data


def _playback_state(app):
    player = app.player
    playlist = app.playlist
    return {
        "current_song": _song_to_ai_dict(playlist.current_song),
        "player_state": player.state.name,
        "volume": player.volume,
        "position": player.position,
        "duration": player.duration,
    }


def _playback_result(app, action: str, message: str = ""):
    return {
        "ok": True,
        "action": action,
        **_playback_state(app),
        "message": message,
    }


@tool
def playback_get_state(runtime: ToolRuntime) -> dict:
    """Get current playback state, current song, and volume."""
    app = runtime.context.app
    return _playback_result(app, "get_state")


@tool
def playback_next_track(runtime: ToolRuntime) -> dict:
    """Play the next track in the current playlist."""
    app = runtime.context.app
    app.playlist.next()
    return _playback_result(app, "next_track")


@tool
def playback_previous_track(runtime: ToolRuntime) -> dict:
    """Play the previous track in the current playlist."""
    app = runtime.context.app
    app.playlist.previous()
    return _playback_result(app, "previous_track")


@tool
def playback_pause(runtime: ToolRuntime) -> dict:
    """Pause playback."""
    app = runtime.context.app
    app.player.pause()
    return _playback_result(app, "pause")


@tool
def playback_resume(runtime: ToolRuntime) -> dict:
    """Resume playback."""
    app = runtime.context.app
    app.player.resume()
    return _playback_result(app, "resume")


@tool
def playback_toggle(runtime: ToolRuntime) -> dict:
    """Toggle between playing and paused states."""
    app = runtime.context.app
    app.player.toggle()
    return _playback_result(app, "toggle")


@tool
def playback_stop(runtime: ToolRuntime) -> dict:
    """Stop playback."""
    app = runtime.context.app
    app.player.stop()
    return _playback_result(app, "stop")


@tool
def playback_set_volume(volume: int, runtime: ToolRuntime) -> dict:
    """Set playback volume from 0 to 100.

    :param volume: Target volume percentage. Values outside 0-100 are clamped.
    """
    app = runtime.context.app
    app.player.volume = _clamp_volume(volume)
    return _playback_result(app, "set_volume")


@tool
def playback_adjust_volume(delta: int, runtime: ToolRuntime) -> dict:
    """Adjust playback volume by a relative delta.

    :param delta: Positive or negative volume change.
    """
    app = runtime.context.app
    app.player.volume = _clamp_volume(app.player.volume + delta)
    return _playback_result(app, "adjust_volume")


playback_tools = [
    playback_get_state,
    playback_next_track,
    playback_previous_track,
    playback_pause,
    playback_resume,
    playback_toggle,
    playback_stop,
    playback_set_volume,
    playback_adjust_volume,
]
