from fuocore.models import BaseModel, ModelType
from fuocore.models import resolve, Resolver


IMG_DATA = b'img data'


class XAlbumModel(BaseModel):
    source = 'fake'  # FakeProvider in conftest

    class Meta:
        model_type = ModelType.album.value
        fields = ['name', 'songs', 'desc', 'img']
        paths = [
            '/img/data',
        ]

    def resolve__img_data(self, **kwargs):
        return IMG_DATA


def test_resolve(event_loop, library):
    Resolver.loop = event_loop
    Resolver.library = library

    album = XAlbumModel()
    result = resolve('/img/data', model=album)
    assert result == IMG_DATA
