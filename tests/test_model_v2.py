from feeluown.library import SongModel, BriefSongModel, BriefAlbumModel, \
    BriefArtistModel


def test_cast_old_model_to_new_model(song):
    brief_song = BriefSongModel.from_orm(song)
    brief_song.title == 'hello world'


def test_song_model():
    identifier = '1'
    title = 'Moon River'
    brief_song = BriefSongModel(identifier=identifier, title=title)
    brief_album = BriefAlbumModel(identifier='1', name='Film', artists_name='Audrey')
    brief_artist = BriefAlbumModel(identifier='1', name='Audrey')
    # song should be created
    song = SongModel(identifier=identifier, title='Moon', album=brief_album,
                     artists=[brief_artist], duration=240000)
    # check song's attribute value
    assert song.artists_name == 'Audrey'
