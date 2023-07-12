from feeluown.media import Media
from feeluown.player import PlaybackMode
from feeluown.gui.uimain.player_bar import PlayerControlPanel
from feeluown.gui.uimain.playlist_overlay import PlaylistOverlay


def test_show_bitrate(qtbot, app_mock):
    app_mock.player.current_media = Media('http://', bitrate=100)
    w = PlayerControlPanel(app_mock)
    qtbot.addWidget(w)
    metadata = {'title': 'xx'}
    w.song_source_label.on_metadata_changed(metadata)
    assert '100kbps' in w.song_source_label.text()


def test_playlist_overlay(qtbot, app_mock):
    app_mock.playlist.playback_mode = PlaybackMode.one_loop
    app_mock.playlist.list.return_value = []
    w = PlaylistOverlay(app_mock)
    qtbot.addWidget(w)
    w.show()
    # assert no error.
    w.show_tab(0)
