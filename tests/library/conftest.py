import pytest

from feeluown.library import (
    AbstractProvider, ProviderV2, ModelType, ProviderFlags as PF,
    AlbumModel,
    Library,
)

SOURCE = 'eee'


class EEEProvider(AbstractProvider, ProviderV2):
    class meta:
        identifier = SOURCE
        name = 'EEE'
        flags = {
            ModelType.album: (PF.model_v2 | PF.get),
        }

    def __init__(self):
        super().__init__()

    @property
    def identifier(self):
        return SOURCE

    @property
    def name(self):
        return '网易云音乐'

    def album_get(self, identifier):
        if identifier == '0':
            return AlbumModel(identifier=identifier,
                              name='0',
                              cover='',
                              description='',
                              songs=[],
                              artists=[])


@pytest.fixture
def eee_provider():
    return EEEProvider()


@pytest.fixture
def xlibrary(eee_provider):
    library = Library()
    library.register(eee_provider)
    return library
