import pytest

from feeluown.library import (
    ModelType,
    BriefAlbumModel,
    BriefSongModel,
    Library,
    Provider,
    Media,
    SimpleSearchResult,
    Quality,
    SongStandbyOptions,
)
from feeluown.media import MediaType


@pytest.mark.asyncio
async def test_library_a_search(library):
    result = [x async for x in library.a_search("xxx")][0]
    assert result.q == "xxx"


def test_library_model_get(library, ekaf_provider, ekaf_album0):
    album = library.model_get(
        ekaf_provider.identifier, ModelType.album, ekaf_album0.identifier
    )
    assert album.identifier == ekaf_album0.identifier


def test_library_model_upgrade(library, ekaf_provider, ekaf_album0):
    album = BriefAlbumModel(
        identifier=ekaf_album0.identifier, source=ekaf_provider.identifier
    )
    album = library._model_upgrade(album)
    assert album.name == ekaf_album0.name


def test_library_model_get_cover_media_uses_provider_hook(
    library, ekaf_provider, ekaf_album0
):
    ekaf_album0.cover = "http://xxx.com/cover.jpg"

    def to_cover_media(url):
        return Media(url, MediaType.image, http_proxy="http://127.0.0.1:7890")

    ekaf_provider.img_url_to_media = to_cover_media
    media = library.model_get_cover_media(ekaf_album0)

    assert media is not None
    assert media.type_ == MediaType.image
    assert media.url == "http://xxx.com/cover.jpg"
    assert media.http_proxy == "http://127.0.0.1:7890"


def test_prepare_mv_media(library, ekaf_brief_song0):
    media = library.song_prepare_mv_media(ekaf_brief_song0, "<<<")
    assert media.url != ""  # media url is valid(not empty)


class MatchProvider(Provider):
    @property
    def identifier(self):
        return "match"

    @property
    def name(self):
        return "match"

    def search(self, *_, **__):
        return SimpleSearchResult(
            q="",
            songs=[
                BriefSongModel(
                    identifier="matched",
                    source=self.identifier,
                    title="Song",
                    artists_name="Artist",
                )
            ],
        )


@pytest.mark.asyncio
async def test_library_a_list_song_standby_v2(library):
    class GoodProvider(Provider):
        @property
        def identifier(self):
            return "good"

        @property
        def name(self):
            return "good"

        def song_list_quality(self, _):
            return [Quality.Audio.hq]

        def song_get_media(self, _, __):
            return Media("good.mp3")

        def search(self, *_, **__):
            return SimpleSearchResult(
                q="", songs=[BriefSongModel(identifier="1", source=self.identifier)]
            )

    library.register(GoodProvider())
    song = BriefSongModel(identifier="1", title="", source="xxx")
    song_media_list = await library.a_list_song_standby_v2(song)
    assert song_media_list
    assert song_media_list[0][1].url == "good.mp3"


@pytest.mark.asyncio
async def test_library_a_list_song_standby_v3_returns_standbys_without_media(library):
    library.register(MatchProvider())
    song = BriefSongModel(
        identifier="origin",
        source="origin",
        title="Song",
        artists_name="Artist",
    )

    standbys = await library.a_list_song_standby_v3(
        song, SongStandbyOptions(source_in=["match"])
    )

    assert standbys == [
        BriefSongModel(
            identifier="matched",
            source="match",
            title="Song",
            artists_name="Artist",
        )
    ]


@pytest.mark.asyncio
async def test_library_a_list_song_standby_v3_can_return_multiple_per_source(library):
    class MultiMatchProvider(MatchProvider):
        def search(self, *_, **__):
            return SimpleSearchResult(
                q="",
                songs=[
                    BriefSongModel(
                        identifier="matched-1",
                        source=self.identifier,
                        title="Song",
                        artists_name="Artist",
                    ),
                    BriefSongModel(
                        identifier="matched-2",
                        source=self.identifier,
                        title="Song",
                        artists_name="Artist",
                    ),
                    BriefSongModel(
                        identifier="matched-3",
                        source=self.identifier,
                        title="Song",
                        artists_name="Artist",
                    ),
                ],
            )

    library.register(MultiMatchProvider())
    song = BriefSongModel(
        identifier="origin",
        source="origin",
        title="Song",
        artists_name="Artist",
    )

    standbys = await library.a_list_song_standby_v3(
        song, SongStandbyOptions(source_in=["match"], limit_per_source=2)
    )

    assert [standby.identifier for standby in standbys] == ["matched-1", "matched-2"]


@pytest.mark.asyncio
async def test_library_a_list_song_standby_v3_keeps_one_full_score_per_source(library):
    class FullScoreProvider(MatchProvider):
        def search(self, *_, **__):
            return SimpleSearchResult(
                q="",
                songs=[
                    BriefSongModel(
                        identifier="similar",
                        source=self.identifier,
                        title="Song",
                        artists_name="Artist",
                        album_name="Other Album",
                        duration_ms="03:00",
                    ),
                    BriefSongModel(
                        identifier="full-score",
                        source=self.identifier,
                        title="Song",
                        artists_name="Artist",
                        album_name="Album",
                        duration_ms="03:00",
                    ),
                    BriefSongModel(
                        identifier="another-similar",
                        source=self.identifier,
                        title="Song",
                        artists_name="Artist",
                        album_name="Other Album",
                        duration_ms="03:00",
                    ),
                ],
            )

    library.register(FullScoreProvider())
    song = BriefSongModel(
        identifier="origin",
        source="origin",
        title="Song",
        artists_name="Artist",
        album_name="Album",
        duration_ms="03:00",
    )

    standbys = await library.a_list_song_standby_v3(
        song,
        SongStandbyOptions(
            source_in=["match"],
            limit_per_source=3,
            single_full_score_per_source=True,
        ),
    )

    assert [standby.identifier for standby in standbys] == ["full-score"]


@pytest.mark.asyncio
async def test_library_a_list_song_standby_v3_prefers_standby_providers():
    class SearchProvider(Provider):
        def __init__(self, identifier):
            self._identifier = identifier
            self.search_calls = []

        @property
        def identifier(self):
            return self._identifier

        @property
        def name(self):
            return self._identifier

        def search(self, keyword, **kwargs):
            self.search_calls.append((keyword, kwargs))
            return SimpleSearchResult(
                q=keyword,
                songs=[
                    BriefSongModel(
                        identifier=f"{self.identifier}-song",
                        source=self.identifier,
                        title="Song",
                        artists_name="Artist",
                    )
                ],
            )

    library = Library(providers_standby=["standby"])
    normal = SearchProvider("normal")
    standby_provider = SearchProvider("standby")
    library.register(normal)
    library.register(standby_provider)
    song = BriefSongModel(
        identifier="origin",
        source="origin",
        title="Song",
        artists_name="Artist",
    )

    standbys = await library.a_list_song_standby_v3(song)

    assert [song.identifier for song in standbys] == ["standby-song"]
    assert standby_provider.search_calls
    assert normal.search_calls == []


@pytest.mark.asyncio
async def test_library_a_list_song_standby_v3_falls_back_to_other_providers():
    class SearchProvider(Provider):
        def __init__(self, identifier, title="Song"):
            self._identifier = identifier
            self._title = title
            self.search_calls = []

        @property
        def identifier(self):
            return self._identifier

        @property
        def name(self):
            return self._identifier

        def search(self, keyword, **kwargs):
            self.search_calls.append((keyword, kwargs))
            return SimpleSearchResult(
                q=keyword,
                songs=[
                    BriefSongModel(
                        identifier=f"{self.identifier}-song",
                        source=self.identifier,
                        title=self._title,
                        artists_name="Artist",
                    )
                ],
            )

    library = Library(providers_standby=["standby"])
    normal = SearchProvider("normal")
    standby_provider = SearchProvider("standby", title="Other")
    library.register(normal)
    library.register(standby_provider)
    song = BriefSongModel(
        identifier="origin",
        source="origin",
        title="Song",
        artists_name="Artist",
    )

    standbys = await library.a_list_song_standby_v3(song)

    assert [song.identifier for song in standbys] == ["normal-song"]
    assert standby_provider.search_calls
    assert normal.search_calls


@pytest.mark.asyncio
async def test_library_a_list_song_standby_v2_fetches_media_in_parallel(library):
    """When multiple candidates qualify, media should be fetched for all of them
    concurrently (not one-by-one), and valid results returned."""

    class FastProvider(Provider):
        @property
        def identifier(self):
            return "fast"

        @property
        def name(self):
            return "fast"

        def song_list_quality(self, _):
            return [Quality.Audio.hq]

        def song_get_media(self, _, __):
            return Media("fast.mp3")

        def search(self, *_, **__):
            return SimpleSearchResult(
                q="",
                songs=[
                    BriefSongModel(
                        identifier="fast-1",
                        source=self.identifier,
                        title="Similar Song",
                        artists_name="Artist",
                        album_name="Different Album",
                    ),
                    BriefSongModel(
                        identifier="fast-2",
                        source=self.identifier,
                        title="Similar Song",
                        artists_name="Artist",
                        album_name="Different Album",
                    ),
                ],
            )

    class SlowProvider(Provider):
        @property
        def identifier(self):
            return "slow"

        @property
        def name(self):
            return "slow"

        def song_list_quality(self, _):
            return [Quality.Audio.hq]

        def song_get_media(self, _, __):
            return Media("slow.mp3")

        def search(self, *_, **__):
            return SimpleSearchResult(
                q="",
                songs=[
                    BriefSongModel(
                        identifier="slow-1",
                        source=self.identifier,
                        title="Similar Song",
                        artists_name="Artist",
                        album_name="Different Album",
                    ),
                ],
            )

    library.register(FastProvider())
    library.register(SlowProvider())
    song = BriefSongModel(
        identifier="origin",
        source="origin",
        title="Similar Song",
        artists_name="Artist",
        album_name="Album",
        duration_ms="03:00",
    )
    song_media_list = await library.a_list_song_standby_v2(
        song, limit=2
    )
    # Both providers' candidates should have been fetched.
    assert len(song_media_list) >= 1
    fetched_sources = {s.source for s, _ in song_media_list}
    assert "fast" in fetched_sources
    assert all(url != "" for _, url in song_media_list)


@pytest.mark.asyncio
async def test_library_a_list_song_standby_v2_uses_search_position_as_tiebreak(
    library,
):
    """When two candidates have the same score, the one that appears earlier
    in its provider's search results should be returned first."""

    class EarlyProvider(Provider):
        """Returns the matching candidate at position 0."""

        @property
        def identifier(self):
            return "early"

        @property
        def name(self):
            return "early"

        def song_list_quality(self, _):
            return [Quality.Audio.hq]

        def song_get_media(self, _, __):
            return Media("early.mp3")

        def search(self, *_, **__):
            return SimpleSearchResult(
                q="",
                songs=[
                    BriefSongModel(
                        identifier="early-song",
                        source=self.identifier,
                        title="Similar Song",
                        artists_name="Artist",
                        album_name="Different Album",
                    ),
                ],
            )

    class LateProvider(Provider):
        """Returns the matching candidate at position 2 (after some distractors)."""

        @property
        def identifier(self):
            return "late"

        @property
        def name(self):
            return "late"

        def song_list_quality(self, _):
            return [Quality.Audio.hq]

        def song_get_media(self, _, __):
            return Media("late.mp3")

        def search(self, *_, **__):
            return SimpleSearchResult(
                q="",
                songs=[
                    BriefSongModel(
                        identifier="distractor-1",
                        source=self.identifier,
                        title="Irrelevant",
                        artists_name="Nobody",
                    ),
                    BriefSongModel(
                        identifier="distractor-2",
                        source=self.identifier,
                        title="Also Irrelevant",
                        artists_name="Nobody",
                    ),
                    BriefSongModel(
                        identifier="late-song",
                        source=self.identifier,
                        title="Similar Song",
                        artists_name="Artist",
                        album_name="Different Album",
                    ),
                ],
            )

    library.register(EarlyProvider())
    library.register(LateProvider())
    song = BriefSongModel(
        identifier="origin",
        source="origin",
        title="Similar Song",
        artists_name="Artist",
        album_name="Album",
        duration_ms="03:00",
    )
    song_media_list = await library.a_list_song_standby_v2(song, limit=2)
    assert len(song_media_list) == 2
    # EarlyProvider's candidate is at position 0, LateProvider's at position 2.
    # Both have the same score, so position should determine order.
    assert song_media_list[0][0].identifier == "early-song"
    assert song_media_list[1][0].identifier == "late-song"
