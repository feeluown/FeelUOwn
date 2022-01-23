from feeluown.models import BaseModel, ModelType, resolve, Resolver, reverse
from feeluown.library.provider import DummySongModel, DummyAlbumModel, DummyArtistModel


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


def test_reverse():
    artist = DummyArtistModel(identifier=1, name='孙燕姿')
    album = DummyAlbumModel(identifier=1, name='逆光', artists=[artist])
    song = DummySongModel(identifier=1,
                          title='我怀念的',
                          artists=[artist],
                          duration=0,
                          album=album)

    # reverse various song model
    assert reverse(song, as_line=True) == \
        'fuo://dummy/songs/1\t# 我怀念的 - 孙燕姿 - 逆光 - 00:00'
    song_with_no_artist_album = DummySongModel(identifier=1,
                                               title='我怀念的')
    assert reverse(song_with_no_artist_album, as_line=True) == \
        'fuo://dummy/songs/1\t# 我怀念的 - "" - "" - 00:00'
    song_with_nothing = DummySongModel(identifier=1)
    assert reverse(song_with_nothing, as_line=True) == \
        'fuo://dummy/songs/1\t# "" - "" - "" - 00:00'

    song_display = DummySongModel.create_by_display(identifier=1)
    assert reverse(song_display, as_line=True) == \
        'fuo://dummy/songs/1'

    # reverse various album model
    album_with_nothing = DummyAlbumModel(identifier=1)
    assert reverse(album_with_nothing, as_line=True) == \
        'fuo://dummy/albums/1'
    album_with_no_artist = DummyAlbumModel(identifier=1, name='逆光')
    assert reverse(album_with_no_artist, as_line=True) == \
        'fuo://dummy/albums/1\t# 逆光'
    assert reverse(album, as_line=True) == \
        'fuo://dummy/albums/1\t# 逆光 - 孙燕姿'
