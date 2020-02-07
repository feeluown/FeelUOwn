from feeluown.fm import FM
from feeluown.player import Playlist, PlaylistMode


def test_fm_activate_and_deactivate(app_mock, song, mocker):
    mock_fetch = mocker.MagicMock(return_value=[song])
    app_mock.playlist = Playlist(app_mock)
    fm = FM(app_mock)
    fm.activate(mock_fetch)
    assert app_mock.playlist.mode is PlaylistMode.fm
    assert app_mock.task_mgr.get_or_create.called

    fm.deactivate()
    assert app_mock.playlist.mode is PlaylistMode.normal


def test_when_playlist_fm_mode_exited(app_mock, song, mocker):
    mock_fetch = mocker.MagicMock()
    app_mock.playlist = Playlist(app_mock)
    fm = FM(app_mock)
    fm.activate(mock_fetch)
    app_mock.playlist.mode = PlaylistMode.normal
    assert fm._activated is False  # noqa
