from marshmallow import Schema, post_load, fields


class NeteaseSongSchema(Schema):
    identifier = fields.Int(requried=True, load_from='id')
    title = fields.Str(required=True, load_from='name')
    duration = fields.Float(required=True)
    url = fields.Str(allow_none=True)
    album = fields.Nested('NeteaseAlbumSchema')
    artists = fields.List(fields.Nested('NeteaseArtistSchema'))

    @post_load
    def create_model(self, data):
        album = data['album']
        artists = data['artists']

        # 在所有的接口中，song.album.songs 要么是一个空列表，
        # 要么是 null，这里统一置为 None。
        album.songs = None

        # 在有的接口中（比如歌单列表接口），album cover 的值是不对的，
        # 它会指向的是一个网易云默认的灰色图片，我们将其设置为 None，
        # artist cover 也有类似的问题。
        album.cover = None

        if artists:
            for artist in artists:
                artist.cover = None

        return NSongModel(**data)


class NeteaseAlbumSchema(Schema):
    identifier = fields.Int(required=True, load_from='id')
    name = fields.Str(required=True)
    cover = fields.Str(load_from='picUrl', allow_none=True)
    songs = fields.List(fields.Nested('NeteaseSongSchema'))
    artists = fields.List(fields.Nested('NeteaseArtistSchema'))

    @post_load
    def create_model(self, data):
        return NAlbumModel(**data)


class NeteaseArtistSchema(Schema):
    identifier = fields.Int(required=True, load_from='id')
    name = fields.Str()
    cover = fields.Str(load_from='picUrl', allow_none=True)
    songs = fields.List(fields.Nested('NeteaseSongSchema'))

    @post_load
    def create_model(self, data):
        return NArtistModel(**data)


class NeteasePlaylistSchema(Schema):
    identifier = fields.Int(required=True, load_from='id')
    uid = fields.Int(required=True, load_from='userId')
    name = fields.Str(required=True)
    desc = fields.Str(required=True, allow_none=True, load_from='description')
    cover = fields.Url(required=True, load_from='coverImgUrl')
    # songs field maybe null, though it can't be null in model
    songs = fields.List(fields.Nested(NeteaseSongSchema),
                        load_from='tracks',
                        allow_none=True)

    @post_load
    def create_model(self, data):
        if data.get('desc') is None:
            data['desc'] = ''
        return NPlaylistModel(**data)


class NeteaseUserSchema(Schema):
    identifier = fields.Int(required=True, load_from='id')
    name = fields.Str(required=True)
    playlists = fields.List(fields.Nested(NeteasePlaylistSchema))
    fav_playlists = fields.List(fields.Nested(NeteasePlaylistSchema))
    cookies = fields.Dict()

    @post_load
    def create_model(self, data):
        return NUserModel(**data)


from .models import NAlbumModel
from .models import NArtistModel
from .models import NPlaylistModel
from .models import NSongModel
from .models import NUserModel
