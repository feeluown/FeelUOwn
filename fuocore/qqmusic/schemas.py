from marshmallow import Schema, fields, post_load


class _SongArtistSchema(Schema):
    identifier = fields.Int(load_from='id', required=True)
    name = fields.Str(load_from='name', required=True)

    @post_load
    def create_model(self, data):
        return QQArtistModel(**data)


class _SongAlbumSchema(Schema):
    identifier = fields.Int(load_from='id', required=True)
    name = fields.Str(load_from='name', required=True)

    @post_load
    def create_model(self, data):
        return QQAlbumModel(**data)


class QQSongSchema(Schema):
    identifier = fields.Int(load_from='songid', required=True)
    mid = fields.Str(load_from='songmid', required=True)
    duration = fields.Float(load_from='interval', required=True)
    title = fields.Str(load_from='songname', required=True)

    artists = fields.List(fields.Nested('_SongArtistSchema'), load_from='singer')

    album_id = fields.Int(load_from='albumid', required=True)
    album_name = fields.Str(load_from='albumname', required=True)

    @post_load
    def create_model(self, data):
        song = QQSongModel(identifier=data['identifier'],
                           mid=data['mid'],
                           duration=data['duration'] * 1000,
                           title=data['title'],
                           artists=data.get('artists'))
        song.album = QQAlbumModel(identifier=data['album_id'],
                                  name=data['album_name'])
        return song


class _ArtistSongSchema(Schema):
    value = fields.Nested(QQSongSchema, load_from='musicData')


class QQArtistSchema(Schema):
    """歌手详情 Schema、歌曲歌手简要信息 Schema"""

    identifier = fields.Int(load_from='singer_id', required=True)
    mid = fields.Str(load_from='singer_mid', required=True)
    name = fields.Str(load_from='singer_name', required=True)

    desc = fields.Str(load_from='SingerDesc')
    songs = fields.List(fields.Nested(_ArtistSongSchema), load_from='list')

    @post_load
    def create_model(self, data):
        if data['songs']:
            data['songs'] = [song['value'] for song in data['songs']]
        return QQArtistModel(**data)


class QQAlbumSchema(Schema):
    identifier = fields.Int(load_from='id', required=True)
    mid = fields.Str(load_from='mid', required=True)
    name = fields.Str(required=True)
    desc = fields.Str(required=True)

    artist_id = fields.Int(load_from='singerid', required=True)
    artist_name = fields.Str(load_from='singername', required=True)

    # 有的专辑歌曲列表为 null，比如：fuo://qqmusic/albums/8623
    songs = fields.List(fields.Nested(QQSongSchema), load_from='list', allow_none=True)

    @post_load
    def create_model(self, data):
        artist = QQArtistModel(identifier=data['artist_id'],
                               name=data['artist_name'])
        album = QQAlbumModel(identifier=data['identifier'],
                             mid=data['mid'],
                             name=data['name'],
                             desc=data['desc'],
                             songs=data['songs'] or [],
                             artists=[artist])
        return album


class QQSongDetailSchema(Schema):
    identifier = fields.Int(load_from='id', required=True)
    mid = fields.Str(required=True)
    duration = fields.Float(load_from='interval', required=True)
    title = fields.Str(load_from='name', required=True)
    artists = fields.List(fields.Nested('_SongArtistSchema'), load_from='singer')
    album = fields.Nested('_SongAlbumSchema', required=True)

    @post_load
    def create_model(self, data):
        song = QQSongModel(identifier=data['identifier'],
                           mid=data['mid'],
                           duration=data['duration'] * 1000,
                           title=data['title'],
                           artists=data.get('artists'),
                           album=data.get('album'),)
        return song


from .models import (
    QQArtistModel,
    QQSongModel,
    QQAlbumModel,
)  # noqa
