import inspect
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import feeluown.mcpserver as mcpserver
from feeluown.player import PlaybackMode, State
from feeluown.library import SearchType, Collection, CollectionType


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


class ReaderProvider:
    identifier = "fake"

    def __init__(self):
        self.last_playlist = None
        self.last_album = None
        self.last_artist = None

    def playlist_create_songs_rd(self, playlist):
        self.last_playlist = playlist
        return ["ps1", "ps2"]

    def album_create_songs_rd(self, album):
        self.last_album = album
        return ["as1", "as2"]

    def artist_create_songs_rd(self, artist):
        self.last_artist = artist
        return ["ars1", "ars2"]

    def artist_create_albums_rd(self, artist):
        self.last_artist = artist
        return ["ara1", "ara2"]

    def artist_create_contributed_albums_rd(self, artist):
        self.last_artist = artist
        return ["arc1", "arc2"]


class CurrentUserProvider:
    identifier = "fake"

    def __init__(self):
        self.last_radio_count = None
        self.user = SimpleNamespace(marker="user")

    def has_current_user(self):
        return True

    def get_current_user(self):
        return self.user

    def get_current_user_or_none(self):
        return self.user

    def current_user_list_playlists(self):
        return ["upl1", "upl2"]

    def current_user_list_radio_songs(self, count):
        self.last_radio_count = count
        return ["urs1", "urs2"]

    def current_user_fav_create_songs_rd(self):
        return ["ufs1", "ufs2"]

    def current_user_fav_create_albums_rd(self):
        return ["ufa1", "ufa2"]

    def current_user_fav_create_artists_rd(self):
        return ["ufar1", "ufar2"]

    def current_user_fav_create_playlists_rd(self):
        return ["ufp1", "ufp2"]

    def current_user_fav_create_videos_rd(self):
        return ["ufv1", "ufv2"]


class PlaylistMutationProvider:
    identifier = "fake"

    def __init__(self):
        self.last_create_name = None
        self.last_delete_id = None
        self.last_add_args = None
        self.last_remove_args = None

    def playlist_create_by_name(self, name):
        self.last_create_name = name
        return SimpleNamespace(marker="playlist-created")

    def playlist_delete(self, playlist_id):
        self.last_delete_id = playlist_id
        return True

    def playlist_add_song(self, playlist, song):
        self.last_add_args = (playlist, song)
        return True

    def playlist_remove_song(self, playlist, song):
        self.last_remove_args = (playlist, song)
        return True


class SongCommentsProvider:
    identifier = "fake"

    def __init__(self):
        self.last_song = None

    def song_list_hot_comments(self, song):
        self.last_song = song
        return ["c1", "c2"]


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


def test_playlist_add_model_json_success(mocker, app):
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    payload = {
        "__type__": "feeluown.library.BriefSongModel",
        "identifier": "song1",
        "source": "fake",
        "title": "demo",
        "artists_name": "artist",
        "album_name": "album",
        "duration_ms": "03:20",
    }

    assert mcpserver.playlist_add_model_json(payload) is True
    app.playlist.add.assert_called_once()
    model = app.playlist.add.call_args.args[0]
    assert model.identifier == "song1"
    assert model.title == "demo"


def test_playlist_add_model_json_invalid_payload(mocker, app):
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    assert mcpserver.playlist_add_model_json({}) is False
    app.playlist.add.assert_not_called()


def test_playlist_add_model_json_unsupported_model(mocker, app):
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    payload = {
        "__type__": "feeluown.library.BriefArtistModel",
        "identifier": "artist1",
        "source": "fake",
        "name": "demo-artist",
    }

    assert mcpserver.playlist_add_model_json(payload) is False
    app.playlist.add.assert_not_called()


def test_playlist_play_model_json_success(mocker, app):
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    payload = {
        "__type__": "feeluown.library.BriefVideoModel",
        "identifier": "video1",
        "source": "fake",
        "title": "demo-video",
    }

    assert mcpserver.playlist_play_model_json(payload) is True
    app.playlist.play_model.assert_called_once()
    model = app.playlist.play_model.call_args.args[0]
    assert model.identifier == "video1"
    assert model.title == "demo-video"


def test_playlist_play_model_json_invalid_payload(mocker, app):
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    assert mcpserver.playlist_play_model_json({}) is False
    app.playlist.play_model.assert_not_called()


def test_playlist_play_model_json_unsupported_model(mocker, app):
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    payload = {
        "__type__": "feeluown.library.BriefArtistModel",
        "identifier": "artist1",
        "source": "fake",
        "name": "demo-artist",
    }

    assert mcpserver.playlist_play_model_json(payload) is False
    app.playlist.play_model.assert_not_called()


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
    mocker.patch(
        "feeluown.mcpserver.serialize",
        side_effect=lambda _, items: list(items),
    )

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
    mocker.patch(
        "feeluown.mcpserver.serialize",
        side_effect=lambda _, items: list(items),
    )

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
    mocker.patch(
        "feeluown.mcpserver.serialize",
        side_effect=lambda _, items: list(items),
    )

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


def test_provider_playlist_list_songs(mocker, app):
    provider = ReaderProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch(
        "feeluown.mcpserver.serialize",
        side_effect=lambda _, items: list(items),
    )

    payload = mcpserver.provider_playlist_list_songs("fake", "pl1", limit=1)

    assert payload == ["ps1"]
    playlist_arg = provider.last_playlist
    assert playlist_arg.identifier == "pl1"
    assert playlist_arg.source == "fake"


def test_provider_album_list_songs(mocker, app):
    provider = ReaderProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch(
        "feeluown.mcpserver.serialize",
        side_effect=lambda _, items: list(items),
    )

    payload = mcpserver.provider_album_list_songs("fake", "al1", limit=1)

    assert payload == ["as1"]
    album_arg = provider.last_album
    assert album_arg.identifier == "al1"
    assert album_arg.source == "fake"


@pytest.mark.parametrize(
    ("tool_name", "expected"),
    [
        ("provider_artist_list_songs", "ars1"),
        ("provider_artist_list_albums", "ara1"),
        ("provider_artist_list_contributed_albums", "arc1"),
    ],
)
def test_provider_artist_list_tools(mocker, app, tool_name, expected):
    provider = ReaderProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch(
        "feeluown.mcpserver.serialize",
        side_effect=lambda _, items: list(items),
    )

    tool = getattr(mcpserver, tool_name)
    payload = tool("fake", "ar1", limit=1)

    assert payload == [expected]
    artist_arg = provider.last_artist
    assert artist_arg.identifier == "ar1"
    assert artist_arg.source == "fake"


def test_provider_playlist_list_songs_unsupported(mocker, app):
    provider = ProviderWithoutGets()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    assert mcpserver.provider_playlist_list_songs("fake", "pl1") is None


def test_provider_current_user_get(mocker, app):
    provider = CurrentUserProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch(
        "feeluown.mcpserver.serialize",
        side_effect=lambda _, obj: {"marker": obj.marker},
    )

    payload = mcpserver.provider_current_user_get("fake")

    assert payload == {"marker": "user"}


def test_provider_current_user_list_tools(mocker, app):
    provider = CurrentUserProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch(
        "feeluown.mcpserver.serialize",
        side_effect=lambda _, items: list(items),
    )

    payload = mcpserver.provider_current_user_list_playlists("fake", limit=1)
    assert payload == ["upl1"]

    payload = mcpserver.provider_current_user_list_radio_songs(
        "fake",
        count=3,
        limit=1,
    )
    assert payload == ["urs1"]
    assert provider.last_radio_count == 3


@pytest.mark.parametrize(
    ("tool_name", "expected"),
    [
        ("provider_current_user_fav_list_songs", "ufs1"),
        ("provider_current_user_fav_list_albums", "ufa1"),
        ("provider_current_user_fav_list_artists", "ufar1"),
        ("provider_current_user_fav_list_playlists", "ufp1"),
        ("provider_current_user_fav_list_videos", "ufv1"),
    ],
)
def test_provider_current_user_fav_list_tools(mocker, app, tool_name, expected):
    provider = CurrentUserProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch(
        "feeluown.mcpserver.serialize",
        side_effect=lambda _, items: list(items),
    )

    tool = getattr(mcpserver, tool_name)
    payload = tool("fake", limit=1)

    assert payload == [expected]


def test_provider_current_user_get_unsupported(mocker, app):
    provider = ProviderWithoutGets()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    assert mcpserver.provider_current_user_get("fake") is None


def test_provider_playlist_mutation_tools(mocker, app):
    provider = PlaylistMutationProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch(
        "feeluown.mcpserver.serialize",
        side_effect=lambda _, obj: {"marker": obj.marker},
    )

    payload = mcpserver.provider_playlist_create_by_name("fake", "my-list")
    assert payload == {"marker": "playlist-created"}
    assert provider.last_create_name == "my-list"

    payload = mcpserver.provider_playlist_delete("fake", "pl1")
    assert payload is True
    assert provider.last_delete_id == "pl1"

    payload = mcpserver.provider_playlist_add_song("fake", "pl1", "so1")
    assert payload is True
    playlist_arg, song_arg = provider.last_add_args
    assert playlist_arg.identifier == "pl1"
    assert playlist_arg.source == "fake"
    assert song_arg.identifier == "so1"
    assert song_arg.source == "fake"

    payload = mcpserver.provider_playlist_remove_song("fake", "pl1", "so1")
    assert payload is True
    playlist_arg, song_arg = provider.last_remove_args
    assert playlist_arg.identifier == "pl1"
    assert playlist_arg.source == "fake"
    assert song_arg.identifier == "so1"
    assert song_arg.source == "fake"


def test_provider_playlist_mutation_tools_unsupported(mocker, app):
    provider = ProviderWithoutGets()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    assert mcpserver.provider_playlist_create_by_name("fake", "n") is None
    assert mcpserver.provider_playlist_delete("fake", "pl1") is None
    assert mcpserver.provider_playlist_add_song("fake", "pl1", "so1") is None
    assert mcpserver.provider_playlist_remove_song("fake", "pl1", "so1") is None


def test_provider_song_list_hot_comments(mocker, app):
    provider = SongCommentsProvider()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)
    mocker.patch(
        "feeluown.mcpserver.serialize",
        side_effect=lambda _, items: list(items),
    )

    payload = mcpserver.provider_song_list_hot_comments("fake", "so1", limit=1)

    assert payload == ["c1"]
    song_arg = provider.last_song
    assert song_arg.identifier == "so1"
    assert song_arg.source == "fake"


def test_provider_song_list_hot_comments_unsupported(mocker, app):
    provider = ProviderWithoutGets()
    app.library.get.return_value = provider
    mocker.patch("feeluown.mcpserver.get_app", return_value=app)

    assert mcpserver.provider_song_list_hot_comments("fake", "so1") is None
