import pytest

from feeluown.library import (
    ModelType, BriefAlbumModel, BriefSongModel, Provider, Media,
    SimpleSearchResult, Quality
)


@pytest.mark.asyncio
async def test_library_a_search(library):
    result = [x async for x in library.a_search('xxx')][0]
    assert result.q == 'xxx'


def test_library_model_get(library, ekaf_provider, ekaf_album0):
    album = library.model_get(ekaf_provider.identifier,
                              ModelType.album,
                              ekaf_album0.identifier)
    assert album.identifier == ekaf_album0.identifier


def test_library_model_upgrade(library, ekaf_provider, ekaf_album0):
    album = BriefAlbumModel(identifier=ekaf_album0.identifier,
                            source=ekaf_provider.identifier)
    album = library._model_upgrade(album)
    assert album.name == ekaf_album0.name


def test_prepare_mv_media(library, ekaf_brief_song0):
    media = library.song_prepare_mv_media(ekaf_brief_song0, '<<<')
    assert media.url != ''  # media url is valid(not empty)


@pytest.mark.asyncio
async def test_library_a_list_song_standby_v2(library):

    class GoodProvider(Provider):
        @property
        def identifier(self):
            return 'good'

        @property
        def name(self):
            return 'good'

        def song_list_quality(self, _):
            return [Quality.Audio.hq]

        def song_get_media(self, _, __):
            return Media('good.mp3')

        def search(self, *_, **__):
            return SimpleSearchResult(
                q='',
                songs=[BriefSongModel(identifier='1', source=self.identifier)]
            )

    library.register(GoodProvider())
    song = BriefSongModel(identifier='1', title='', source='xxx')
    song_media_list = await library.a_list_song_standby_v2(song)
    assert song_media_list
    assert song_media_list[0][1].url == 'good.mp3'
