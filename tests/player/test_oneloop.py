from unittest.mock import MagicMock
from feeluown.player.playlist import PlaybackMode, Playlist


def test_oneloop():
    app = MagicMock()
    playlist = Playlist(app)
    playlist.playback_mode = PlaybackMode.one_loop
    app.player.set_loop.assert_called_with(True)
