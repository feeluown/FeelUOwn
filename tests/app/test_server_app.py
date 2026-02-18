import types

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


@pytest.mark.asyncio
async def test_server_app_run_with_mcp_enabled(signal_aio_support, args, config, mocker,
                                               noharm):
    config.MODE = AppMode.server
    config.ENABLE_MCP_SERVER = True
    config.MCP_PORT = 32335

    app = ServerApp(args, config)

    mocker.patch.object(app, "get_listen_addr", return_value="127.0.0.1")
    mocker.patch.object(
        app.rpc_server, "run", new=lambda *_args, **_kwargs: "rpc-task"
    )
    mocker.patch.object(
        app.pubsub_server, "run", new=lambda *_args, **_kwargs: "pubsub-task"
    )
    mocker.patch(
        "feeluown.app.server_app.run_nowplaying_server",
        new=lambda *_args, **_kwargs: "np-task",
    )
    mock_create_task = mocker.patch("feeluown.app.server_app.asyncio.create_task")

    run_mcp_server = mocker.Mock(return_value="mcp-task")
    fake_mcpserver = types.ModuleType("feeluown.mcpserver")
    fake_mcpserver.run_mcp_server = run_mcp_server
    mocker.patch.dict("sys.modules", {"feeluown.mcpserver": fake_mcpserver})

    app.run()

    run_mcp_server.assert_called_once_with("127.0.0.1", 32335)
    assert mock_create_task.call_count == 4


@pytest.mark.asyncio
async def test_server_app_run_with_mcp_import_error(
    signal_aio_support,
    args,
    config,
    mocker,
    noharm,
):
    config.MODE = AppMode.server
    config.ENABLE_MCP_SERVER = True

    app = ServerApp(args, config)

    mocker.patch.object(app, "get_listen_addr", return_value="127.0.0.1")
    mocker.patch.object(
        app.rpc_server, "run", new=lambda *_args, **_kwargs: "rpc-task"
    )
    mocker.patch.object(
        app.pubsub_server, "run", new=lambda *_args, **_kwargs: "pubsub-task"
    )
    mocker.patch(
        "feeluown.app.server_app.run_nowplaying_server",
        new=lambda *_args, **_kwargs: "np-task",
    )
    mock_create_task = mocker.patch("feeluown.app.server_app.asyncio.create_task")
    mock_logger_error = mocker.patch("feeluown.app.server_app.logger.error")
    mocker.patch.dict("sys.modules", {"feeluown.mcpserver": None})

    app.run()

    mock_logger_error.assert_called_once()
    assert "can't enable mcp server" in mock_logger_error.call_args.args[0]
    assert mock_create_task.call_count == 3
