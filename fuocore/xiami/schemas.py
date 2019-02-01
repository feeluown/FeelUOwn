from marshmallow import Schema, fields, post_load


class ArtistSchema(Schema):
    """歌手详情 Schema、歌曲歌手简要信息 Schema
    """

    identifier = fields.Int(load_from='artistId', required=True)
    name = fields.Str(load_from='artistName', required=True)
    cover = fields.Str(load_from='artistLogo', missing=None)
    desc = fields.Str(load_from='description', missing=None)

    @post_load
    def create_model(self, data):
        return XArtistModel(**data)


class AlbumSchema(Schema):
    """专辑详情 Schema

    >>> import json
    >>> with open('data/fixtures/xiami/album.json') as f:
    ...     data = json.load(f)
    ...     schema = AlbumSchema(strict=True)
    ...     album, _ = schema.load(data)
    >>> album.identifier
    2100387382
    """
    identifier = fields.Int(load_from='albumId', required=True)
    name = fields.Str(load_from='albumName', required=True)
    cover = fields.Str(load_from='albumLogo', required=True)

    songs = fields.List(fields.Nested('NestedSongSchema'))
    artists = fields.List(fields.Nested(ArtistSchema), load_from='artists')
    desc = fields.Str(load_from='description')

    @post_load
    def create_model(self, data):
        return XAlbumModel(**data)


class SongSchema(Schema):
    """歌曲详情 Schema

    >>> import json
    >>> with open('data/fixtures/xiami/song.json') as f:
    ...     data = json.load(f)
    ...     schema = SongSchema(strict=True)
    ...     song, _ = schema.load(data)
    >>> song.url
    ''
    """
    identifier = fields.Int(load_from='songId', required=True)
    title = fields.Str(load_from='songName', required=True)
    # FIXME: 有的歌曲没有 length 字段
    duration = fields.Str(load_from='length', missing='0')

    url = fields.Str(load_from='listenFile', missing='')
    # files = fields.List(fields.Dict, load_from='listenFiles', missing=[])

    # XXX: 这里暂时用 singerVOs 来表示歌曲的 artist，即使虾米接口中
    # 也会包含歌曲 artistVOs 信息
    artists = fields.List(fields.Nested(ArtistSchema), load_from='singerVOs', required=True)

    album_id = fields.Int(load_from='albumId', required=True)
    album_name = fields.Str(load_from='albumName', required=True)
    album_cover = fields.Str(load_from='albumLogo', required=True)

    @post_load
    def create_model(self, data):
        album = XAlbumModel(identifier=data['album_id'],
                            name=data['album_name'],
                            cover=data['album_cover'])
        # files = data['files']
        # files = sorted(files, key=lambda f: f['quality'], reverse=True)
        # if files:
        #     url = files[0]['url']
        # else:
        #     url = ''  # 设置为空，代表这首歌没有合适的 url
        song = XSongModel(identifier=data['identifier'],
                          title=data['title'],
                          url=data['url'],
                          duration=int(data['duration']),
                          album=album,
                          artists=data['artists'])
        return song


class NestedSongSchema(SongSchema):
    """搜索结果中歌曲 Schema、专辑/歌手详情中歌曲 Schema

    通过 search 得到的 Song 的结构和通过 song_detail 获取的 Song 的结构不一样

    search 接口得到的 Song 没有 listenFile 字段，但是可能会有 listenFiles 字段，
    有的话，取 listenFiles 中最高质量的播放链接作为音乐的 url。
    """
    files = fields.List(fields.Dict, load_from='listenFiles', missing=[])

    @post_load
    def create_model(self, data):
        song = super().create_model(data)
        files = sorted(data['files'], key=lambda f: f['quality'], reverse=True)
        if files:
            url = files[0]['listenFile']
        else:
            url = ''  # 设置为空，代表这首歌没有合适的 url
        song.url = url
        return song


class PlaylistSchema(Schema):
    """歌单 Schema

    >>> import json
    >>> with open('data/fixtures/xiami/playlist.json') as f:
    ...     data = json.load(f)
    ...     schema = PlaylistSchema(strict=True)
    ...     playlist, _ = schema.load(data)
    >>> len(playlist.songs)
    100
    """
    identifier = fields.Str(load_from='listId', required=True)
    uid = fields.Int(load_from='userId', required=True)
    name = fields.Str(load_from='collectName', required=True)
    cover = fields.Str(load_from='collectLogo', required=True)
    songs = fields.List(fields.Nested(NestedSongSchema), missing=None)
    desc = fields.Str(load_from='description', missing=None)

    @post_load
    def create_model(self, data):
        return XPlaylistModel(**data)


class SongSearchSchema(Schema):
    """歌曲搜索结果 Schema"""
    songs = fields.List(fields.Nested(NestedSongSchema), required=True)

    @post_load
    def create_model(self, data):
        return XSearchModel(**data)


class UserSchema(Schema):
    identifier = fields.Int(load_from='userId')
    name = fields.Str(load_from='nickName')
    access_token = fields.Str(load_from='accessToken')

    @post_load
    def create_model(self, data):
        return XUserModel(**data)


from .models import (
    XAlbumModel,
    XArtistModel,
    XPlaylistModel,
    XSongModel,
    XSearchModel,
    XUserModel,
)  # noqa
