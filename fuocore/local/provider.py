# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
"""
TODO: 这个模块中目前逻辑非常多，包括音乐目录扫描、音乐库的构建等小部分，
这些小部分理论都可以从中拆除。
"""

import base64
import logging
import os
import re

from fuzzywuzzy import process
from marshmallow.exceptions import ValidationError
from mutagen import MutagenError
from mutagen.mp3 import EasyMP3
from mutagen.easymp4 import EasyMP4
from fuocore.provider import AbstractProvider
from fuocore.utils import elfhash
from fuocore.utils import log_exectime


logger = logging.getLogger(__name__)


def scan_directory(directory, exts=None, depth=2):
    exts = exts or ['mp3', 'fuo']
    if depth < 0:
        return []

    media_files = []
    if not os.path.exists(directory):
        return []
    for path in os.listdir(directory):
        path = os.path.join(directory, path)
        if os.path.isdir(path):
            files = scan_directory(path, exts, depth - 1)
            media_files.extend(files)
        elif os.path.isfile(path):
            if path.split('.')[-1] in exts:
                media_files.append(path)
    return media_files


def gen_id(s):
    return str(elfhash(base64.b64encode(bytes(s, 'utf-8'))))


def create_artist(identifier, name):
    return LArtistModel(identifier=identifier,
                        name=name,
                        songs=[],
                        albums=[],
                        desc='',
                        cover='',)


def create_album(identifier, name):
    return LAlbumModel(identifier=identifier,
                       name=name,
                       songs=[],
                       artists=[],
                       desc='',
                       cover='',)


def add_song(fpath, g_songs, g_artists, g_albums):
    """
    parse music file metadata with Easymp3 and return a song
    model.
    """
    try:
        if fpath.endswith('mp3') or fpath.endswith('ogg') or fpath.endswith('wma'):
            metadata = EasyMP3(fpath)
        elif fpath.endswith('m4a'):
            metadata = EasyMP4(fpath)
    except MutagenError as e:
        logger.exception('Mutagen parse metadata failed, ignore.')
        return None

    metadata_dict = dict(metadata)
    for key in metadata.keys():
        metadata_dict[key] = metadata_dict[key][0]
    if 'title' not in metadata_dict:
        title = fpath.rsplit('/')[-1].split('.')[0]
        metadata_dict['title'] = title
    metadata_dict.update(dict(
        url=fpath,
        duration=metadata.info.length * 1000  # milesecond
    ))
    schema = EasyMP3MetadataSongSchema(strict=True)
    try:
        data, _ = schema.load(metadata_dict)
    except ValidationError:
        logger.exeception('解析音乐文件({}) 元数据失败'.format(fpath))
        return

    # NOTE: use {title}-{artists_name}-{album_name} as song identifier
    title = data['title']
    album_name = data['album_name']
    artist_name_list = [
        name.strip()
        for name in re.split(r'[,&]', data['artists_name'])]
    artists_name = ','.join(artist_name_list)
    duration = data['duration']
    album_artist_name = data['album_artist_name']

    # 生成 song model
    # 用来生成 id 的字符串应该尽量减少无用信息，这样或许能减少 id 冲突概率
    song_id_str = ''.join([title, artists_name, album_name, str(int(duration))])
    song_id = gen_id(song_id_str)
    if song_id not in g_songs:
        # 剩下 album, lyric 三个字段没有初始化
        song = LSongModel(identifier=song_id,
                          artists=[],
                          title=title,
                          url=fpath,
                          duration=duration,
                          comments=[],
                          # 下面这些字段不向外暴露
                          genre=data['genre'],
                          cover=data['cover'],
                          date=data['date'],
                          desc=data['desc'],
                          disc=data['disc'],
                          track=data['track'])
        g_songs[song_id] = song
    else:
        song = g_songs[song_id]
        logger.debug('Duplicate song: %s %s', song.url, fpath)
        return

    # 生成 album artist model
    album_artist_id = gen_id(album_artist_name)
    if album_artist_id not in g_artists:
        album_artist = create_artist(album_artist_id, album_artist_name)
        g_artists[album_artist_id] = album_artist
    else:
        album_artist = g_artists[album_artist_id]

    # 生成 album model
    album_id_str = album_name + album_artist_name
    album_id = gen_id(album_id_str)
    if album_id not in g_albums:
        album = create_album(album_id, album_name)
        g_albums[album_id] = album
    else:
        album = g_albums[album_id]

    # 处理专辑的歌手信息和歌曲信息，专辑歌手的专辑列表信息
    if album not in album_artist.albums:
        album_artist.albums.append(album)
    if album_artist not in album.artists:
        album.artists.append(album_artist)
    if song not in album.songs:
        album.songs.append(song)

    # 处理歌曲的歌手和专辑信息，以及歌手的歌曲列表
    song.album = album
    for artist_name in artist_name_list:
        artist_id = gen_id(artist_name)
        if artist_id in g_artists:
            artist = g_artists[artist_id]
        else:
            artist = create_artist(identifier=artist_id, name=artist_name)
            g_artists[artist_id] = artist
        if artist not in song.artists:
            song.artists.append(artist)
        if song not in artist.songs:
            artist.songs.append(song)


class Library:
    DEFAULT_MUSIC_FOLDER = os.path.expanduser('~') + '/Music'

    def __init__(self):
        self._songs = {}
        self._albums = {}
        self._artists = {}

    def list_songs(self):
        return list(self._songs.values())

    def get_song(self, identifier):
        return self._songs.get(identifier)

    def get_album(self, identifier):
        return self._albums.get(identifier)

    def get_artist(self, identifier):
        return self._artists.get(identifier)

    @log_exectime
    def scan(self, paths=None, depth=2):
        """scan media files in all paths
        """
        song_exts = ['mp3', 'ogg', 'wma', 'm4a']
        exts = song_exts
        paths = paths or [Library.DEFAULT_MUSIC_FOLDER]
        depth = depth if depth <= 3 else 3
        media_files = []
        for directory in paths:
            logger.debug('正在扫描目录(%s)...', directory)
            media_files.extend(scan_directory(directory, exts, depth))
        logger.info('共扫描到 %d 个音乐文件，准备将其录入本地音乐库', len(media_files))

        for fpath in media_files:
            add_song(fpath, self._songs, self._artists, self._albums)
        logger.info('录入本地音乐库完毕')

    def sortout(self):
        for album in self._albums.values():
            try:
                album.songs.sort(key=lambda x: (int(x.disc.split('/')[0]), int(x.track.split('/')[0])))
            except Exception as e:
                logger.exception('Sort album songs failed.')

        for artist in self._artists.values():
            if artist.albums:
                artist.albums.sort(key=lambda x: (x.songs[0].date is None, x.songs[0].date), reverse=True)
            if artist.songs:
                artist.songs.sort(key=lambda x: x.title)


class LocalProvider(AbstractProvider):

    def __init__(self):
        super().__init__()

        self.library = Library()

    def scan(self, paths=None, depth=3):
        self.library.scan(paths, depth)
        self.library.sortout()

    @property
    def identifier(self):
        return 'local'

    @property
    def name(self):
        return '本地音乐'

    @property
    def songs(self):
        return self.library.list_songs()

    @log_exectime
    def search(self, keyword, **kwargs):
        limit = kwargs.get('limit', 10)
        repr_song_map = dict()
        for song in self.songs:
            key = song.title + ' ' + song.artists_name + str(song.identifier)
            repr_song_map[key] = song
        choices = repr_song_map.keys()
        result = process.extract(keyword, choices, limit=limit)
        result_songs = []
        for each, score in result:
            # if score > 80, keyword is almost included in song key
            if score > 80:
                result_songs.append(repr_song_map[each])
        return LSearchModel(q=keyword, songs=result_songs)


provider = LocalProvider()

from .schemas import EasyMP3MetadataSongSchema
from .models import (
    LSearchModel,
    LSongModel,
    LAlbumModel,
    LArtistModel,
)
