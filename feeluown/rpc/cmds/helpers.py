"""
feeluown.cmds.helper
~~~~~~~~~~~~~~~~~~~

良好的用文字展示一个对象

展示的时候需要注意以下几点：
1. 让 awk、grep 等 shell 工具容易处理

TODO: 让代码长得更好看
"""

from itertools import chain

from feeluown.models.uri import reverse


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


def show_song(song, uri_length=None, brief=False, fetch=False):
    """以一行文字的方式显示一首歌的信息

    :param uri_length: 控制 song uri 的长度
    :param brief: 是否只显示简要信息
    :param fetch: 是否在线请求未初始化的属性
    """
    artists_name = song.artists_name if fetch else song.artists_name_display
    song_title = song.title if fetch else song.title_display
    title = _fit_text(song_title or '', 18, filling=False)
    album_name = song.album_name if fetch else song.album_name_display

    song_uri = reverse(song)
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
    album_uri = reverse(song.album)
    artists_uri = ','.join(reverse(artist) for artist in song.artists)
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


def show_songs(songs):
    uri_length = max((len(reverse(song)) for song in songs)) if songs else None
    return '\n'.join([show_song(song, uri_length=uri_length, brief=True)
                      for song in songs])


def show_artist(artist, brief=False):
    if brief:
        return '{uri}\t# {name}'.format(
            uri=reverse(artist),
            name=artist.name)
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
    if brief:
        return '{uri}\t# {name} - {artists_name}'.format(
            uri=reverse(album),
            name=album.name,
            artists_name=album.artists_name
        )

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


def show_playlists(playlists):
    return '\n'.join((show_playlist(playlist, brief=True)
                      for playlist in playlists))


def show_user(user):
    parts = [
        'name:        {}'.format(user.name),
        'playlists::',
    ]
    parts += ['\t' + show_playlist(p, brief=True) for p in user.playlists]
    return '\n'.join(parts)


def show_search(search):
    """show search result model"""

    song_part = map(lambda so: show_song(so, brief=True),
                    search.songs or [])
    pl_part = map(lambda pl: show_playlist(pl, brief=True),
                  search.playlists or [])
    ar_part = map(lambda ar: show_artist(ar, brief=True),
                  search.artists or [])
    al_part = map(lambda al: show_album(al, brief=True),
                  search.albums or [])
    return '\n'.join(chain(song_part, ar_part, al_part, pl_part))
