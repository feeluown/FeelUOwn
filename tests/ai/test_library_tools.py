from types import SimpleNamespace

import pytest

from feeluown.ai.tools.library import DEFAULT_SEARCH_TIMEOUT, library_search
from feeluown.ai.tools.songs import play_song_by_uri
from feeluown.library import (
    AlbumModel,
    ArtistModel,
    BriefAlbumModel,
    BriefArtistModel,
    Library,
    Provider,
    SimpleSearchResult,
    SongModel,
    VideoModel,
    reverse,
    parse_line,
    ModelType,
)


class FakeRuntime:
    def __init__(self, app, copilot=None):
        self.context = SimpleNamespace(
            app=app,
            copilot=copilot or FakeCopilot(),
        )


class FakeCopilot:
    def __init__(self):
        self.models = {}

    def cache_model(self, model):
        self.models[reverse(model)] = model

    def get_song_by_uri(self, uri):
        model, _ = parse_line(uri)
        if ModelType(model.meta.model_type) != ModelType.song:
            raise ValueError
        return self.models[reverse(model)]


class FakeProvider(Provider):
    @property
    def identifier(self):
        return "fake"

    @property
    def name(self):
        return "Fake"

    def __init__(self):
        super().__init__()
        self.artist_brief = BriefArtistModel(
            identifier="artist-1",
            source=self.identifier,
            name="Mary",
        )
        self.album_brief = BriefAlbumModel(
            identifier="album-1",
            source=self.identifier,
            name="Album",
            artists_name="Mary",
        )
        self.song = SongModel(
            identifier="song-1",
            source=self.identifier,
            title="Song",
            album=self.album_brief,
            artists=[self.artist_brief],
            duration=180000,
        )
        self.artist = ArtistModel(
            identifier="artist-1",
            source=self.identifier,
            name="Mary",
            pic_url="https://example.com/artist.jpg",
            aliases=[],
            hot_songs=[self.song],
            description="Artist description",
        )
        self.album = AlbumModel(
            identifier="album-1",
            source=self.identifier,
            name="Album",
            cover="https://example.com/album.jpg",
            artists=[self.artist_brief],
            songs=[self.song],
            song_count=1,
            description="Album description",
        )
        self.video = VideoModel(
            identifier="video-1",
            source=self.identifier,
            title="Video",
            artists=[self.artist_brief],
            duration=200000,
            cover="https://example.com/video.jpg",
        )

    def search(self, keyword, **kwargs):
        return SimpleSearchResult(
            q=keyword,
            source=self.identifier,
            songs=[self.song],
            albums=[self.album],
            artists=[self.artist],
            videos=[self.video],
        )


def create_runtime():
    library = Library()
    provider = FakeProvider()
    library.register(provider)
    app = SimpleNamespace(library=library)
    return FakeRuntime(app)


class CapturingLibrary:
    def __init__(self):
        self.search_kwargs = None

    async def a_search(self, keyword, **kwargs):
        self.search_kwargs = {"keyword": keyword, **kwargs}
        yield SimpleSearchResult(q=keyword, source="fake")


class MultiResultLibrary:
    def __init__(self):
        self.song1 = SongModel(
            identifier="song-1",
            source="fake",
            title="Song 1",
            album=None,
            artists=[],
            duration=180000,
        )
        self.song2 = SongModel(
            identifier="song-2",
            source="fake",
            title="Song 2",
            album=None,
            artists=[],
            duration=180000,
        )
        self.song3 = SongModel(
            identifier="song-3",
            source="other",
            title="Song 3",
            album=None,
            artists=[],
            duration=180000,
        )

    async def a_search(self, keyword, **kwargs):
        yield SimpleSearchResult(
            q=keyword,
            source="fake",
            songs=[self.song1, self.song2],
        )
        yield SimpleSearchResult(
            q=keyword,
            source="other",
            songs=[self.song3],
        )


@pytest.mark.asyncio
async def test_library_search_tool_returns_online_resource_results():
    runtime = create_runtime()

    result = await library_search.coroutine(
        keyword="Song",
        type_in="song,artist",
        limit_per_type=1,
        runtime=runtime,
    )

    assert result["ok"] is True
    assert result["action"] == "search"
    assert result["data"]["timeout"] == DEFAULT_SEARCH_TIMEOUT
    assert "song_count" not in result["data"]
    assert "songs" not in result["data"]
    search_result = result["data"]["results"][0]
    assert search_result["source"] == "fake"
    assert search_result["songs"][0]["source"] == "fake"
    assert search_result["songs"][0]["model_type"] == "song"
    assert search_result["songs"][0]["uri"] == "fuo://fake/songs/song-1"
    assert "artifact_song_position" not in search_result["songs"][0]
    assert search_result["artists"][0]["uri"] == "fuo://fake/artists/artist-1"
    assert "fuo://fake/songs/song-1" in runtime.context.copilot.models


@pytest.mark.asyncio
async def test_library_search_tool_passes_timeout_to_library():
    library = CapturingLibrary()
    runtime = FakeRuntime(SimpleNamespace(library=library))

    result = await library_search.coroutine(
        keyword="Song",
        timeout=2.5,
        runtime=runtime,
    )

    assert result["ok"] is True
    assert result["data"]["timeout"] == 2.5
    assert library.search_kwargs["timeout"] == 2.5


@pytest.mark.asyncio
async def test_library_search_song_can_be_played_by_uri():
    library = MultiResultLibrary()
    playlist = SimpleNamespace(play_model=lambda song: setattr(playlist, "song", song))
    runtime = FakeRuntime(SimpleNamespace(library=library, playlist=playlist))

    search_result = await library_search.coroutine(
        keyword="Song",
        runtime=runtime,
    )
    song_uris = [
        song["uri"]
        for result in search_result["data"]["results"]
        for song in result["songs"]
    ]
    play_result = play_song_by_uri.func(
        song_uri=song_uris[2],
        runtime=runtime,
    )

    assert song_uris == [
        "fuo://fake/songs/song-1",
        "fuo://fake/songs/song-2",
        "fuo://other/songs/song-3",
    ]
    assert play_result["ok"] is True
    assert playlist.song is library.song3
