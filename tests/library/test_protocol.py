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

    # BriefAlbumProtocol
    assert isinstance(brief_album, BriefAlbumProtocol)

    # BriefArtistprotocol
    assert isinstance(brief_artist, BriefArtistProtocol)

    # BriefSongProtocol
    assert isinstance(brief_song, BriefSongModel)
    assert isinstance(song, BriefSongProtocol)

    # SongProtocol
    assert isinstance(song, SongProtocol)

    # BriefUserProtocol
    assert isinstance(brief_user, BriefUserProtocol)
    assert isinstance(user, BriefUserProtocol)

    # UserProtocol
    assert isinstance(user, UserProtocol)

    # VideoProtocol
    assert isinstance(video, VideoProtocol)
