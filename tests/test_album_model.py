from fuocore.models import AlbumModel, AlbumType


def test_album_model_default_type():
    album = AlbumModel(identifier=1)
    assert album.type == AlbumType.unknown

    album2 = AlbumModel.create_by_display(identifier=2)
    assert album2.type == AlbumType.unknown
