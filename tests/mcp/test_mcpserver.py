import inspect
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import feeluown.mcpserver as mcpserver
from feeluown.player import PlaybackMode, State
from feeluown.library import ResolveFailed, SearchType, Collection, CollectionType


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


class ProviderWithGets:
    identifier = "fake"
    name = "FAKE"

    def __init__(self):
        self._models = {
            "song": SimpleNamespace(marker="song"),
            "album": SimpleNamespace(marker="album"),
            "artist": SimpleNamespace(marker="artist"),
            "playlist": SimpleNamespace(marker="playlist"),
            "video": SimpleNamespace(marker="video"),
        }

    def song_get(self, _):
        return self._models["song"]

    def album_get(self, _):
        return self._models["album"]

    def artist_get(self, _):
        return self._models["artist"]

    def playlist_get(self, _):
        return self._models["playlist"]

    def video_get(self, _):
        return self._models["video"]


class ProviderWithoutGets:
    identifier = "fake"
    name = "FAKE"


class RecProvider:
    identifier = "fake"

    def rec_list_daily_songs(self):
        return ["a", "b"]

    def rec_list_daily_playlists(self):
        return ["a", "b"]

    def rec_list_daily_albums(self):
        return ["a", "b"]


class RecCollectionsProvider:
    identifier = "fake"

    def __init__(self, collection):
        self.collection = collection
        self.last_limit = None

    def rec_list_collections(self, limit=None):
        self.last_limit = limit
        return [self.collection]


class RecSingleProvider:
    identifier = "fake"

    def __init__(self, collection):
        self.collection = collection

    def rec_a_collection_of_songs(self):
        return self.collection

    def rec_a_collection_of_videos(self):
        return self.collection


class ToplistProvider:
    identifier = "fake"

    def __init__(self):
        self.last_toplist_id = None

    def toplist_list(self):
        return ["a", "b"]

    def toplist_get(self, toplist_id):
        self.last_toplist_id = toplist_id
        return SimpleNamespace(marker="toplist")


class SongProvider:
    identifier = "fake"

    def __init__(self):
        self.last_song = None

    def song_get_lyric(self, song):
        self.last_song = song
        return SimpleNamespace(marker="lyric")

    def song_get_web_url(self, song):
        self.last_song = song
        return "https://example.com/song"

    def song_get_mv(self, song):
        self.last_song = song
        return SimpleNamespace(marker="mv")

    def song_list_similar(self, song):
        self.last_song = song
        return ["s1", "s2"]


class VideoProvider:
    identifier = "fake"

    def __init__(self):
        self.last_video = None

    def video_get_web_url(self, video):
        self.last_video = video
        return "https://example.com/video"


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
    mock_run = mocker.patch.object(mcpserver.mcp, "run_streamable_http_async")

    result = mcpserver.run_mcp_server("0.0.0.0", 12345, debug=True)

    assert mcpserver.mcp.settings.host == "0.0.0.0"
    assert mcpserver.mcp.settings.port == 12345
    assert mcpserver.mcp.settings.debug is True
    assert mcpserver.mcp.settings.log_level == "DEBUG"
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


def test_provider_search(mocker, app):
    provider = MagicMock()
    provider.identifier = "fake"
    provider.search.return_value = MagicMock()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch(
        "feeluown.mcpserver.serialize", return_value={"songs": ["a", "b"]}
    )

    payload = mcpserver.provider_search("fake", "hello", limit=1)

    assert payload == [
        {"type": "song", "source": "fake", "result": {"songs": ["a"]}}
    ]
    provider.search.assert_called_once_with(keyword="hello", type_=SearchType.so)


@pytest.mark.parametrize(
    ("tool_name", "marker"),
    [
        ("provider_song_get", "song"),
        ("provider_album_get", "album"),
        ("provider_artist_get", "artist"),
        ("provider_playlist_get", "playlist"),
        ("provider_video_get", "video"),
    ],
)
def test_provider_model_get_tools(mocker, app, tool_name, marker):
    provider = ProviderWithGets()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    def fake_serialize(_, obj):
        return {"marker": obj.marker}

    mocker.patch("feeluown.mcpserver.serialize", side_effect=fake_serialize)

    tool = getattr(mcpserver, tool_name)
    payload = tool("fake", "id")

    assert payload == {"marker": marker}


def test_provider_song_get_unsupported(mocker, app):
    provider = ProviderWithoutGets()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    assert mcpserver.provider_song_get("fake", "id") is None


@pytest.mark.parametrize(
    ("tool_name", "method_name"),
    [
        ("provider_rec_list_daily_songs", "rec_list_daily_songs"),
        ("provider_rec_list_daily_playlists", "rec_list_daily_playlists"),
        ("provider_rec_list_daily_albums", "rec_list_daily_albums"),
    ],
)
def test_provider_rec_list_daily_tools(mocker, app, tool_name, method_name):
    provider = RecProvider()
    assert hasattr(provider, method_name)
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch("feeluown.mcpserver.serialize", side_effect=lambda _, items: list(items))

    tool = getattr(mcpserver, tool_name)
    payload = tool("fake", limit=1)

    assert payload == ["a"]


def test_provider_rec_list_collections(mocker, app):
    collection = Collection(
        name="Daily",
        type_=CollectionType.only_songs,
        models=["m1", "m2"],
        description="desc",
    )
    provider = RecCollectionsProvider(collection)
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch("feeluown.mcpserver.serialize", side_effect=lambda _, items: list(items))

    payload = mcpserver.provider_rec_list_collections("fake", limit=2)

    assert payload == [
        {
            "name": "Daily",
            "type": "only_songs",
            "description": "desc",
            "models": ["m1", "m2"],
        }
    ]
    assert provider.last_limit == 2


@pytest.mark.parametrize(
    ("tool_name", "method_name"),
    [
        ("provider_rec_a_collection_of_songs", "rec_a_collection_of_songs"),
        ("provider_rec_a_collection_of_videos", "rec_a_collection_of_videos"),
    ],
)
def test_provider_rec_single_collection(mocker, app, tool_name, method_name):
    collection = Collection(
        name="Pick",
        type_=CollectionType.only_videos,
        models=["m1"],
        description="desc",
    )
    provider = RecSingleProvider(collection)
    assert hasattr(provider, method_name)
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch("feeluown.mcpserver.serialize", side_effect=lambda _, items: list(items))

    tool = getattr(mcpserver, tool_name)
    payload = tool("fake")

    assert payload == {
        "name": "Pick",
        "type": "only_videos",
        "description": "desc",
        "models": ["m1"],
    }


def test_provider_toplist_tools(mocker, app):
    provider = ToplistProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    def fake_serialize(_, obj):
        if isinstance(obj, list):
            return list(obj)
        return {"marker": obj.marker}

    mocker.patch("feeluown.mcpserver.serialize", side_effect=fake_serialize)

    payload = mcpserver.provider_toplist_list("fake", limit=1)
    assert payload == ["a"]

    payload = mcpserver.provider_toplist_get("fake", "id")
    assert payload == {"marker": "toplist"}
    assert provider.last_toplist_id == "id"


def test_provider_song_tools(mocker, app):
    provider = SongProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    def fake_serialize(_, obj):
        if isinstance(obj, list):
            return list(obj)
        return {"marker": obj.marker}

    mocker.patch("feeluown.mcpserver.serialize", side_effect=fake_serialize)

    payload = mcpserver.provider_song_get_lyric("fake", "song1")
    assert payload == {"marker": "lyric"}
    song_arg = provider.last_song
    assert song_arg.identifier == "song1"
    assert song_arg.source == "fake"

    payload = mcpserver.provider_song_get_web_url("fake", "song1")
    assert payload == "https://example.com/song"
    song_arg = provider.last_song
    assert song_arg.identifier == "song1"
    assert song_arg.source == "fake"

    payload = mcpserver.provider_song_get_mv("fake", "song1")
    assert payload == {"marker": "mv"}
    song_arg = provider.last_song
    assert song_arg.identifier == "song1"
    assert song_arg.source == "fake"

    payload = mcpserver.provider_song_list_similar("fake", "song1", limit=1)
    assert payload == ["s1"]
    song_arg = provider.last_song
    assert song_arg.identifier == "song1"
    assert song_arg.source == "fake"


def test_provider_video_get_web_url(mocker, app):
    provider = VideoProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    payload = mcpserver.provider_video_get_web_url("fake", "video1")

    assert payload == "https://example.com/video"
    video_arg = provider.last_video
    assert video_arg.identifier == "video1"
    assert video_arg.source == "fake"
