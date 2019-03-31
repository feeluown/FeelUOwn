"""
fuocore.cmds.helper
~~~~~~~~~~~~~~~~~~~

良好的用文字展示一个对象
TODO: 负责返回 json 对象

展示的时候需要注意以下几点：
1. 让 awk、grep 等 shell 工具容易处理

TODO: 让代码长得更好看
"""

from fuocore.models import ModelType
import json
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)

TYPE_NS_MAP = {
    ModelType.song: 'songs',
    ModelType.artist: 'artists',
    ModelType.album: 'albums',
    ModelType.playlist: 'playlists',
    ModelType.user: 'users',
    ModelType.lyric: 'lyrics',
}
URL_SCHEME = 'fuo'
NS_TYPE_MAP = {
    value: key
    for key, value in TYPE_NS_MAP.items()
}

class ReturnStatus(IntEnum):
    success = 0
    fail = 1
    error = -1

RETURN_STATUS_MAP = {
    ReturnStatus.success: 'success',
    ReturnStatus.fail: 'fail',
    ReturnStatus.error: 'error'
}

class ReturnMessage:
    def __init__(self, status=ReturnStatus.success, data={}, msg="", output_format="json"):
        self.status = status
        self.data = data
        self.msg = msg
        self.output_format = output_format
    def dumps(self):
        msg_dict = {"status": RETURN_STATUS_MAP[self.status]}
        logger.debug(self.data)
        if self.data:
            msg_dict["data"] = self.data
        if self.msg:
            msg_dict["msg"] = self.msg
        if self.output_format == "json":
            return json.dumps(msg_dict)
        else:
            return

def get_url(model):
    source = model.source
    ns = TYPE_NS_MAP[model.meta.model_type]
    identifier = model.identifier
    return 'fuo://{}/{}/{}'.format(source, ns, identifier)


def _fit_text(text, length, filling=True):
    """裁剪或者填补字符串，控制其显示的长度

    >>> _fit_text('12345', 6)
    '12345 '
    >>> _fit_text('哈哈哈哈哈s', 6)  # doctest: -ELLIPSIS
    '哈哈 …'
    >>> _fit_text('哈s哈哈哈哈s', 6)  # doctest: -ELLIPSIS
    '哈s哈…'
    >>> _fit_text('sssss', 5)
    'sssss'

    FIXME: 这样可能会截断一些英文词汇
    """
    assert 80 >= length >= 5

    text_len = 0
    len_index_map = {}
    for i, c in enumerate(text):
        # FIXME: 根据目前少量观察，在大部分字体下，
        # \u4e00 后面的字符宽度是英文字符两倍
        if ord(c) < 19968:  # ord(u'\u4e00')
            text_len += 1
            len_index_map[text_len] = i
        else:
            text_len += 2
            len_index_map[text_len] = i

    if text_len <= length:
        if filling:
            return text + (length - text_len) * ' '
        return text

    remain = length - 1
    if remain in len_index_map:
        return text[:(len_index_map[remain] + 1)] + '…'
    else:
        return text[:(len_index_map[remain - 1] + 1)] + ' …'


def show_song(song, uri_length=None, brief=False):
    """以一行文字的方式显示一首歌的信息

    :param uri_length: 控制 song uri 的长度
    :param brief: 是否只显示简要信息
    """
    artists_name = song.artists_name_display
    title = _fit_text(song.title_display, 18, filling=False)
    album_name = song.album_name_display

    song_uri = get_url(song)
    if uri_length is not None:
        song_uri = _fit_text(song_uri, uri_length)

    if brief:
        artists_name = _fit_text(artists_name, 20, filling=False)
        s = '{song}\t# {title} - {artists_name}'.format(
            song=song_uri,
            title=title,
            artists_name=artists_name)
        return s

    # XXX: 这个操作可能会产生网络请求
    album_uri = get_url(song.album)
    artists_uri = ','.join(get_url(artist) for artist in song.artists)
    msgs = (
        'provider:     {}'.format(song.source),
        '     uri:     {}'.format(song_uri),
        '   title:     {}'.format(song.title),
        'duration:     {}'.format(song.duration),
        '     url:     {}'.format(song.url),
        ' artists:     {}\t# {}'.format(artists_uri, artists_name),
        '   album:     {}\t# {}'.format(album_uri, album_name),
    )
    return '\n'.join(msgs)

def show_song_json(song, brief=False):
    # 返回描述歌曲的 json 对象
    artists_name = song.artists_name_display
    title = song.title_display
    album_name = song.album_name_display

    song_uri = get_url(song)

    result = ReturnMessage()

    if brief:
        data = dict()
        data["song"] = song_uri
        data["title"] = title
        data["artists_name"] = artists_name
        result.data = data
        return result.dumps()

    # XXX: 这个操作可能会产生网络请求
    album_uri = get_url(song.album)
    artists_uri = [get_url(artist) for artist in song.artists]
    data = dict()
    data["provider"] = song.source
    data["uri"] = song_uri
    data["title"] = song.title
    data["duration"] = song.duration
    data["url"] = song.url
    data["artists_uri"] = artists_uri
    data["artists_name"] = artists_name
    data["album_uri"] = album_uri
    data["album_name"] = album_name
    result.data = data
    return result.dumps()

def show_songs(songs):
    uri_length = max((len(get_url(song)) for song in songs)) if songs else None
    return '\n'.join([show_song(song, uri_length=uri_length, brief=True)
                      for song in songs])


def show_artist(artist):
    msgs = [
        'provider:      {}'.format(artist.source),
        'identifier:    {}'.format(artist.identifier),
        'name:          {}'.format(artist.name),
    ]
    if artist.songs:
        songs_header = ['songs::']
        songs = ['\t' + each for each in show_songs(artist.songs).split('\n')]
        msgs += songs_header
        msgs += songs
    return '\n'.join(msgs)


def show_album(album, brief=False):
    msgs = [
        'provider:      {}'.format(album.source),
        'identifier:    {}'.format(album.identifier),
        'name:          {}'.format(album.name),
    ]
    if album.artists is not None:
        artists = album.artists
        artists_id = ','.join([str(artist.identifier) for artist in artists])
        artists_name = ','.join([artist.name for artist in artists])
        msgs_artists = ['artists:       {}\t#{}'.format(artists_id, artists_name)]
        msgs += msgs_artists
    if not brief:
        msgs_songs_header = ['songs::']
        msgs_songs = ['\t' + each for each in show_songs(album.songs).split('\n')]
        msgs += msgs_songs_header
        msgs += msgs_songs
    return '\n'.join(msgs)


def show_playlist(playlist, brief=False):
    if brief:
        content = '{playlist}\t#{name}'.format(
            playlist=playlist,
            name=playlist.name)
    else:
        parts = [
            'name:        {}'.format(playlist.name),
            'songs::',
        ]
        parts += ['\t' + show_song(song, brief=True) for song in playlist.songs]
        content = '\n'.join(parts)
    return content


def show_user(user):
    parts = [
        'name:        {}'.format(user.name),
        'playlists::',
    ]
    parts += ['\t' + show_playlist(p, brief=True) for p in user.playlists]
    return '\n'.join(parts)
