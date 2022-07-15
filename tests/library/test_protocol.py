from feeluown.library import (
    BriefAlbumModel,
    BriefArtistModel,
    BriefSongModel, SongModel,
    BriefUserModel, UserModel,
    VideoModel,
)
from feeluown.library.model_protocol import (
    BriefAlbumProtocol,
    BriefArtistProtocol,
    BriefSongProtocol, SongProtocol,
    BriefUserProtocol, UserProtocol,
    VideoProtocol,
)
from feeluown.models import (
    AlbumModel as AlbumModelV1,
    ArtistModel as ArtistModelV1,
    SongModel as SongModelV1,
    UserModel as UserModelV1,
)


def test_protocols():
    values = dict(identifier='0', source='test')

    brief_album = BriefAlbumModel(**values)
    brief_artist = BriefArtistModel(**values)
    brief_song = BriefSongModel(**values)
    brief_user = BriefUserModel(**values)

    song = SongModel(artists=[brief_artist],
                     album=brief_album,
                     title='',
                     duration=0,
                     **values)
    user = UserModel(**values)
    video = VideoModel(title='',
                       artists=[],
                       cover='',
                       duration=0,
                       **values)

    album_v1 = AlbumModelV1(**values)
    artist_v1 = ArtistModelV1(**values)
    song_v1 = SongModelV1(**values)
    user_v1 = UserModelV1(**values)

    # BriefAlbumProtocol
    assert isinstance(brief_album, BriefAlbumProtocol)
    assert isinstance(album_v1, BriefAlbumProtocol)

    # BriefArtistprotocol
    assert isinstance(brief_artist, BriefArtistProtocol)
    assert isinstance(artist_v1, BriefArtistProtocol)

    # BriefSongProtocol
    assert isinstance(brief_song, BriefSongModel)
    assert isinstance(song, BriefSongProtocol)
    assert isinstance(song_v1, BriefSongProtocol)

    # SongProtocol
    assert isinstance(song, SongProtocol)
    assert isinstance(song_v1, SongProtocol)

    # BriefUserProtocol
    assert isinstance(brief_user, BriefUserProtocol)
    assert isinstance(user, BriefUserProtocol)
    assert isinstance(user_v1, BriefUserProtocol)

    # UserProtocol
    assert isinstance(user_v1, UserProtocol)
    assert isinstance(user, UserProtocol)

    # VideoProtocol
    assert isinstance(video, VideoProtocol)
