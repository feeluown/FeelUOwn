from types import SimpleNamespace

import pytest

from feeluown.ai.tools.library import DEFAULT_SEARCH_TIMEOUT, library_search
from feeluown.ai.tools.artifacts import play_artifact_song
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
)


class FakeRuntime:
    def __init__(self, app, copilot=None):
        self.context = SimpleNamespace(
            app=app,
            copilot=copilot or FakeCopilot(),
        )


class FakeCopilot:
    def __init__(self):
        self.artifacts = []

    def add_search_result_artifact(self, results, title=""):
        songs = []
        for result in results:
            songs.extend(result.songs)
        artifact = SimpleNamespace(
            identifier=len(self.artifacts) + 1,
            type="search_result",
            title=title or "Search Results",
            songs=songs,
            result=list(results),
        )
        self.artifacts.append(artifact)
        return artifact

    def get_artifact_song(self, artifact_id, song_position):
        artifact = self.artifacts[artifact_id - 1]
        return artifact.songs[song_position - 1]


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
    assert result["data"]["artifact_id"] == 1
    assert "song_count" not in result["data"]
    assert "songs" not in result["data"]
    search_result = result["data"]["results"][0]
    assert search_result["source"] == "fake"
    assert search_result["songs"][0]["source"] == "fake"
    assert search_result["songs"][0]["model_type"] == "song"
    assert search_result["songs"][0]["uri"] == "fuo://fake/songs/song-1"
    assert search_result["songs"][0]["artifact_song_position"] == 1
    assert search_result["artists"][0]["uri"] == "fuo://fake/artists/artist-1"
    artifact = runtime.context.copilot.artifacts[0]
    assert artifact.type == "search_result"
    assert artifact.result[0].songs[0].identifier == "song-1"


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
    assert result["data"]["artifact_id"] == 1
    assert library.search_kwargs["timeout"] == 2.5


@pytest.mark.asyncio
async def test_library_search_artifact_song_can_be_played_by_position():
    library = MultiResultLibrary()
    playlist = SimpleNamespace(play_model=lambda song: setattr(playlist, "song", song))
    runtime = FakeRuntime(SimpleNamespace(library=library, playlist=playlist))

    search_result = await library_search.coroutine(
        keyword="Song",
        runtime=runtime,
    )
    positions = [
        song["artifact_song_position"]
        for result in search_result["data"]["results"]
        for song in result["songs"]
    ]
    play_result = play_artifact_song.func(
        artifact_id=search_result["data"]["artifact_id"],
        song_position=3,
        runtime=runtime,
    )

    assert positions == [1, 2, 3]
    assert play_result["ok"] is True
    assert playlist.song is library.song3
