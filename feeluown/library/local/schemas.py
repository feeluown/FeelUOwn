# -*- coding: utf-8 -*-
from marshmallow import Schema, fields, post_load, EXCLUDE


DEFAULT_TITLE = DEFAULT_ARTIST_NAME = DEFAULT_ALBUM_NAME = 'Unknown'


class EasyMP3MetadataSongSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    """EasyMP3 metadata"""
    url = fields.Str(required=True)
    duration = fields.Float(required=True)
    title = fields.Str(missing=DEFAULT_TITLE)
    artists_name = fields.Str(data_key='artist', missing=DEFAULT_ARTIST_NAME)
    album_name = fields.Str(data_key='album', missing=DEFAULT_ALBUM_NAME)
    album_artist_name = fields.Str(data_key='albumartist', missing=DEFAULT_ARTIST_NAME)
    track = fields.Str(data_key='tracknumber', missing='1/1')
    disc = fields.Str(data_key='discnumber', missing='1/1')
    date = fields.Str(missing='')
    genre = fields.Str(missing='')

    # 本地歌曲目前都不支持描述和封面，将它们设置为空字符串
    desc = fields.Str(missing='')
    cover = fields.Str(missing='')


class FLACMetadataSongSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    """FLAC metadata"""
    url = fields.Str(required=True)
    duration = fields.Float(required=True)
    title = fields.Str(missing=DEFAULT_TITLE)
    artists_name = fields.Str(data_key='artist', missing=DEFAULT_ARTIST_NAME)
    album_name = fields.Str(data_key='album', missing=DEFAULT_ALBUM_NAME)
    album_artist_name = fields.Str(data_key='albumartist', missing=DEFAULT_ARTIST_NAME)
    track = fields.Str(data_key='tracknumber', missing='1')
    disc = fields.Str(data_key='discnumber', missing='1')
    tracktotal = fields.Str(data_key='tracktotal', missing='1')
    disctotal = fields.Str(data_key='disctotal', missing='1')
    date = fields.Str(missing='')
    genre = fields.Str(missing='')

    # 本地歌曲目前都不支持描述和封面，将它们设置为空字符串
    desc = fields.Str(missing='')
    cover = fields.Str(missing='')

    @post_load
    def create_model(self, data, **kwargs):
        data['track'] = '{}/{}'.format(data['track'], data.pop('tracktotal'))
        data['disc'] = '{}/{}'.format(data['disc'], data.pop('disctotal'))
        return data


class APEMetadataSongSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    """APE metadata"""
    url = fields.Str(required=True)
    duration = fields.Float(required=True)
    title = fields.Str(missing=DEFAULT_TITLE)
    artists_name = fields.Str(data_key='artist', missing=DEFAULT_ARTIST_NAME)
    album_name = fields.Str(data_key='album', missing=DEFAULT_ALBUM_NAME)
    album_artist_name = fields.Str(data_key='albumartist', missing=DEFAULT_ARTIST_NAME)
    track = fields.Str(data_key='track', missing='1/1')
    disc = fields.Str(data_key='discnumber', missing='1/1')
    date = fields.Str(missing='')
    genre = fields.Str(missing='')

    # 本地歌曲目前都不支持描述和封面，将它们设置为空字符串
    desc = fields.Str(missing='')
    cover = fields.Str(missing='')
