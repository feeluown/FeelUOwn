import inspect
from unittest.mock import MagicMock

import pytest

import feeluown.mcpserver as mcpserver
from feeluown.player import PlaybackMode, State
from feeluown.library import ResolveFailed


@pytest.fixture
def app():
    app = MagicMock()
    app.player.state = State.playing
    app.player.position = 12.5
    app.player.duration = 200
    app.player.volume = 80
    app.player.current_metadata = MagicMock()
    app.playlist.current_song = MagicMock()
    app.playlist.playback_mode = PlaybackMode.loop
    return app


class FakeProvider:
    class meta:
        identifier = "fake"
        name = "FAKE"

    @property
    def identifier(self):
        return "fake"

    @property
    def name(self):
        return "FAKE"

    def has_current_user(self):
        return False

    def get_current_user(self):
        raise NotImplementedError

    def get_current_user_or_none(self):
        return None


def test_nowplaying_resource(mocker, app):
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch("feeluown.mcpserver.serialize", return_value={"title": "demo"})
    mocker.patch("feeluown.mcpserver.reverse", return_value="fuo://fake/songs/1")

    payload = mcpserver.nowplaying()

    assert payload == {
        "uri": "fuo://fake/songs/1",
        "metadata": {"title": "demo"},
    }


def test_player_status(mocker, app):
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch("feeluown.mcpserver.serialize", return_value={"title": "demo"})
    mocker.patch("feeluown.mcpserver.reverse", return_value="fuo://fake/songs/1")

    payload = mcpserver.player_status()

    assert payload["state"] == "playing"
    assert payload["position"] == 12.5
    assert payload["duration"] == 200
    assert payload["volume"] == 80
    assert payload["playback_mode"] == "loop"
    assert payload["nowplaying"]["uri"] == "fuo://fake/songs/1"


def test_playlist_add_uri_success(mocker, app):
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch("feeluown.mcpserver.resolve", return_value=MagicMock())

    assert mcpserver.playlist_add_uri("fuo://fake/songs/1") is True
    assert app.playlist.add.called


def test_playlist_add_uri_fail(mocker, app):
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch("feeluown.mcpserver.resolve", side_effect=ResolveFailed("bad"))

    assert mcpserver.playlist_add_uri("bad-uri") is False
    assert not app.playlist.add.called


def test_playlist_play_uri(mocker, app):
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch("feeluown.mcpserver.resolve", return_value=MagicMock())

    assert mcpserver.playlist_play_uri("fuo://fake/songs/1") is True
    assert app.playlist.add.called
    assert app.playlist.play_model.called


def test_run_mcp_server_sets_host_port(mocker):
    mock_run = mocker.patch.object(mcpserver.mcp, "run_sse_async")

    result = mcpserver.run_mcp_server("0.0.0.0", 12345)

    assert mcpserver.mcp.settings.host == "0.0.0.0"
    assert mcpserver.mcp.settings.port == 12345
    assert inspect.iscoroutine(result)
    result.close()
    mock_run.assert_called_once()


def test_library_providers(mocker, app):
    provider = FakeProvider()
    app.library.list.return_value = [provider]
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    payload = mcpserver.library_providers()

    assert payload == [{"id": "fake", "name": "FAKE"}]


def test_provider_capabilities(mocker, app):
    provider = FakeProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    payload = mcpserver.provider_capabilities("fake")

    assert payload["id"] == "fake"
    assert "SupportsCurrentUser" in payload["protocols"]
