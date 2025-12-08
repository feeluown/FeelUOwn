import pytest

from feeluown.collection import Collection
from feeluown.ai.prompt import generate_prompt_for_library


@pytest.fixture
def library_mock(song, song1, artist, album):
    library = Collection('/tmp/nonexist.txt')
    for i in range(0, 10):
        library.models.append(song)
        library.models.append(song1)
        library.models.append(artist)
        library.models.append(album)
    return library


@pytest.mark.asyncio
async def test_generate_prompt_for_library(library_mock):
    prompt = await generate_prompt_for_library(library_mock)
    assert 'hello world - mary' in prompt  # song
    assert 'mary\n' in prompt  # artist
    assert 'blue and green' in prompt  # album
