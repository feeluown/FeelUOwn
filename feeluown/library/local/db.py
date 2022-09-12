import base64
import json
import logging
import os
import re
from typing import Optional

from marshmallow.exceptions import ValidationError
from mutagen import MutagenError
from mutagen.mp3 import EasyMP3
from mutagen.easymp4 import EasyMP4
from mutagen.flac import FLAC
from mutagen.apev2 import APEv2

from feeluown.serializers import serialize
from feeluown.utils.utils import elfhash, log_exectime
from feeluown.library import SongModel, AlbumModel, ArtistModel, AlbumType
from feeluown.library import BriefAlbumModel, BriefArtistModel, BriefSongModel
from feeluown.models.uri import reverse

from .lans_helpers import core_lans
from .schemas import (
    EasyMP3MetadataSongSchema,
    FLACMetadataSongSchema,
    APEMetadataSongSchema,
)

logger = logging.getLogger(__name__)
SOURCE = 'local'


def to_brief_song(song):
    return BriefSongModel(
        identifier=song.identifier,
        source=song.source,
        title=song.title,
        artists_name=song.artists_name,
        album_name=song.album_name,
        duration_ms=song.duration_ms,
    )


def to_brief_album(album):
    return BriefAlbumModel(
        identifier=album.identifier,
        source=album.source,
        name=album.name,
        artists_name=album.artists_name,
    )


def to_brief_artist(artist):
    return BriefArtistModel(
        identifier=artist.identifier,
        source=artist.source,
        name=artist.name,
    )


def gen_id(s):
    return str(elfhash(base64.b64encode(bytes(s, 'utf-8'))))


def gen_cover_url(song):
    return reverse(song) + '/cover/data'


def create_artist(identifier, name):
    return ArtistModel(identifier=identifier,
                       source=SOURCE,
                       name=name,
                       pic_url='',
                       aliases=[],
                       hot_songs=[],
                       description='')


def create_album(identifier, name, cover):
    album = AlbumModel(identifier=identifier,
                       source=SOURCE,
                       name=name,
                       cover=cover or '',
                       songs=[],
                       artists=[],
                       description='')
    # guess album type by its name
    #
    # album name which contains following string are `Single`
    #   1. ' - Single'  6+3=9
    #   2. '(single)'   6+2=8
    #   3. '（single）'  6+2=8
    if 'single' in name[-9:].lower():
        album.type = AlbumType.single
    if 'ep' in name[-5:].lower():
        album.type = AlbumType.ep
    return album


def add_song(fpath,
             g_songs, g_artists, g_albums,
             g_file_song,
             lans='auto', delimiter='', expand_artist_songs=False):
    """
    parse music file metadata with Easymp3 and return a song
    model.
    """

    try:
        if fpath.endswith('mp3') or fpath.endswith('ogg') or fpath.endswith('wma'):
            metadata = EasyMP3(fpath)
        elif fpath.endswith('m4a') or fpath.endswith('m4v') or fpath.endswith('mp4'):
            metadata = EasyMP4(fpath)
        elif fpath.endswith('flac'):
            metadata = FLAC(fpath)
        elif fpath.endswith('ape'):
            metadata = APEv2(fpath)
        elif fpath.endswith('wav'):
            metadata = dict()
    except MutagenError as e:
        logger.warning(
            'Mutagen parse metadata failed, ignore.\n'
            'file: {}, exception: {}'.format(fpath, str(e)))
        return None

    metadata_dict = dict(metadata)
    for key in metadata.keys():
        metadata_dict[key] = core_lans(metadata_dict[key][0], lans)
    if 'title' not in metadata_dict:
        title = os.path.split(fpath)[-1].split('.')[0]
        metadata_dict['title'] = core_lans(title, lans)
    metadata_dict.update(dict(
        url=fpath,
        duration=metadata.info.length * 1000  # milesecond
    ))

    try:
        if fpath.endswith('flac'):
            data = FLACMetadataSongSchema().load(metadata_dict)
        elif fpath.endswith('ape'):
            data = APEMetadataSongSchema().load(metadata_dict)
        else:
            data = EasyMP3MetadataSongSchema().load(metadata_dict)
    except ValidationError:
        logger.exception('解析音乐文件({}) 元数据失败'.format(fpath))
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

    # 如果专辑歌手名字是 unknown，并且歌曲的歌手里面有一个非 unknown 的，
    # 就用它作为专辑歌手名字。因为这种情况很可能是元数据不规范造成的。
    if album_artist_name == 'Unknown':
        if artist_name_list:
            for each in artist_name_list:
                if each != 'Unknown':
                    album_artist_name = each

    # 生成 song model
    # 用来生成 id 的字符串应该尽量减少无用信息，这样或许能减少 id 冲突概率
    # 加入分隔符'-'在一定概率上更能确保不发生哈希值重复
    song_id_str = delimiter.join([title, artists_name, album_name, str(int(duration))])
    song_id = gen_id(song_id_str)
    if song_id not in g_songs:
        song = SongModel(identifier=song_id,
                         source=SOURCE,
                         artists=[],
                         title=title,
                         duration=duration,
                         genre=data['genre'],
                         # cover=data['cover'],
                         # date=data['date'],
                         # desc=data['desc'],
                         disc=data['disc'],
                         track=data['track'])
        g_file_song[fpath] = song_id
        g_songs[song_id] = song
    else:
        song = g_songs[song_id]
        logger.warning('Duplicate song: %s', fpath)
        return

    # 生成 album artist model
    album_artist_id = gen_id(album_artist_name)
    if album_artist_id not in g_artists:
        album_artist = create_artist(album_artist_id, album_artist_name)
        g_artists[album_artist_id] = album_artist
    else:
        album_artist = g_artists[album_artist_id]

    # 生成 album model
    album_id_str = delimiter.join([album_name, album_artist_name])
    album_id = gen_id(album_id_str)
    cover = gen_cover_url(song)
    if album_id not in g_albums:
        album = create_album(album_id, album_name, cover)
        g_albums[album_id] = album
    else:
        album = g_albums[album_id]

    # 处理专辑的歌手信息和歌曲信息，专辑歌手的专辑列表信息
    for artist in album.artists:
        if album_artist.identifier == artist.identifier:
            break
    else:
        album.artists.append(to_brief_artist(album_artist))

    if song not in album.songs:
        album.songs.append(song)

    # 处理歌曲的歌手和专辑信息，以及歌手的歌曲列表和参与作品
    song.album = to_brief_album(album)
    for artist_name in artist_name_list:
        artist_id = gen_id(artist_name)
        if artist_id in g_artists:
            artist = g_artists[artist_id]
        else:
            artist = create_artist(identifier=artist_id, name=artist_name)
            g_artists[artist_id] = artist
        if artist not in song.artists:
            song.artists.append(to_brief_artist(artist))
        if song not in artist.hot_songs:
            artist.hot_songs.append(song)

        # 处理歌曲歌手的参与作品信息(不与前面的重复)
        # TODO(this_pr)
        # if album not in artist.albums and album not in artist.contributed_albums:
        #     artist.contributed_albums.append(album)

    # 处理专辑歌手的歌曲信息: 有些作词人出合辑很少出现在歌曲歌手里(可选)
    if expand_artist_songs and song not in album_artist.hot_songs:
        album_artist.hot_songs.append(song)


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


class DB:
    """
    DB manages a fileset and their corresponding models

    the data structure in db file::

        {
          "files": [],
          "songs": []
        }
    """
    def __init__(self, fpath):
        """
        :param filepath: database file path
        """

        self._dirty = False  # whether changes are flushed
        self._fileset = set()  # media files
        self._fpath = fpath

        self._file_song = {}      # {fpath: song_id}
        self._song_file = {}      # {song_id: fpath}
        self._songs = {}          # {song_id: song}
        self._albums = {}         # {album_id: album)
        self._artists = {}        # {artist_id: artist)
        self._artist_albums = {}  # {artist_id: [album...])

    def flush(self):
        """flush the changes into db file"""
        with open(self._fpath, 'w', encoding='utf-8') as f:
            json.dump({
                'version': '1.0',
                'files': list(self._fileset),
                'songs': serialize('json', self._songs),
                'artists': serialize('json', self._artists),
                'albums': serialize('json', self._albums),
            }, f)

    def list_models(self):
        """list all models in database"""
        pass

    def add(self, fpath):
        """add media file to database"""
        add_song(fpath,
                 self._songs, self._artists, self._albums,
                 self._file_song)

    def remove(self, fpath):
        """add media file to database"""

    ############################

    def list_songs(self):
        return list(self._songs.values())

    def list_albums(self):
        return list(self._albums.values())

    def list_artists(self):
        return list(self._artists.values())

    def get_song(self, identifier):
        return self._songs.get(identifier)

    def get_album(self, identifier):
        return self._albums.get(identifier)

    def get_artist(self, identifier):
        return self._artists.get(identifier)

    def get_song_fpath(self, song_id) -> Optional[str]:
        return self._song_file.get(song_id)

    @log_exectime
    def scan(self, config, paths, depth, exts):
        """scan media files in all paths
        """
        media_files = []
        logger.info('start scanning...')
        for directory in paths:
            logger.debug('正在扫描目录(%s)...', directory)
            media_files.extend(scan_directory(directory, exts, depth))
        logger.info(f'scanning finished, {len(media_files)} files in total')

        for fpath in media_files:
            add_song(fpath, self._songs, self._artists, self._albums,
                     self._file_song,
                     config.CORE_LANGUAGE,
                     config.IDENTIFIER_DELIMITER,
                     config.EXPAND_ARTIST_SONGS)
        logger.info('录入本地音乐库完毕')

    def after_scan(self):
        """
        歌曲扫描完成后，对信息进行一些加工，比如
        1. 给专辑歌曲排序
        2. 给专辑和歌手加封面
        """
        def sort_album_func(album):
            if album.songs:
                return (album.songs[0].year != 0, album.songs[0].year)
            return (False, '0')

        for album in self._albums.values():
            try:
                album.songs.sort(key=lambda x: (int(x.disc.split('/')[0]),
                                                int(x.track.split('/')[0])))
                if album.name != 'Unknown':
                    cover = gen_cover_url(album.songs[0])
                    album.cover = cover
            except:  # noqa
                logger.exception('Sort album songs failed.')

        for artist in self._artists.values():
            # if artist.albums:
            #     artist.albums.sort(key=sort_album_func, reverse=True)
            #     artist.cover = artist.albums[0].cover
            # if artist.contributed_albums:
            #     artist.contributed_albums.sort(key=sort_album_func, reverse=True)
            if artist.hot_songs:
                # sort artist.hot_songs
                artist.hot_songs.sort(key=lambda x: x.title)
                # use song cover as artist cover
                # https://github.com/feeluown/feeluown-local/pull/3/files#r362126996
                songs_with_unknown_album = [song for song in artist.hot_songs
                                            if song.album_name == 'Unknown']
                for song in sorted(songs_with_unknown_album,
                                   key=lambda x: (x.year != 0, x.year),
                                   reverse=True):
                    artist.pic_url = gen_cover_url(song)
                    break


        self._song_file = {v: k for k, v in self._file_song.items()}
