import pytest

from feeluown.app import AppMode
from feeluown.app.server_app import ServerApp


@pytest.mark.asyncio
async def test_server_app_initialize(signal_aio_support, args, config, mocker,
                                     noharm):
    config.MODE = AppMode.server

    app = ServerApp(args, config)

    mock_connect_1 = mocker.patch.object(app.live_lyric.sentence_changed, 'connect')
    mock_connect_2 = mocker.patch.object(app.player.position_changed, 'connect')
    mock_connect_3 = mocker.patch.object(app.playlist.song_changed, 'connect')

    app.initialize()

    # live lyric should be initialized properly.
    assert mock_connect_1.called
    assert not mock_connect_2.called
    assert mock_connect_3.called
