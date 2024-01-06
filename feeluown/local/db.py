import base64
import json
import logging
import os
import re
from typing import Optional

from pydantic import ValidationError
from mutagen import MutagenError
from mutagen.mp3 import EasyMP3
from mutagen.easymp4 import EasyMP4
from mutagen.flac import FLAC
from mutagen.apev2 import APEv2File

from feeluown.serializers import serialize
from feeluown.utils.utils import elfhash, log_exectime
from feeluown.utils.lang import can_convert_chinese, convert_chinese
from feeluown.library import SongModel, AlbumModel, ArtistModel, AlbumType
from feeluown.library import BriefAlbumModel, BriefArtistModel, BriefSongModel
from feeluown.library import reverse

from .schemas import EasyMP3Model, APEModel, FLACModel
from .schemas import DEFAULT_ALBUM_NAME


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
        album.type_ = AlbumType.single
    if 'ep' in name[-5:].lower():
        album.type_ = AlbumType.ep
    return album


def read_audio_metadata(fpath, can_convert_chinese=False, lang='auto') -> Optional[dict]:
    """Read metadata, like id3tag, from audio file.

    Return a dict if succeed. Return None when failed, no exception is raised.
    The dict schema is `schemas.Common`.
    """
    try:
        if fpath.endswith('mp3') or fpath.endswith('ogg') or fpath.endswith('wma'):
            metadata = EasyMP3(fpath)
        elif fpath.endswith('m4a') or fpath.endswith('m4v') or fpath.endswith('mp4'):
            metadata = EasyMP4(fpath)
        elif fpath.endswith('flac'):
            metadata = FLAC(fpath)
        elif fpath.endswith('ape'):
            metadata = APEv2File(fpath)
        elif fpath.endswith('wav'):
            metadata = None
        else:  # This branch is actually impossible to reach.
            metadata = None
    except MutagenError as e:
        logger.warning(
            'Mutagen parse metadata failed, ignore.\n'
            'file: {}, exception: {}'.format(fpath, str(e)))
        return

    # For example::
    #
    #   {
    #    'album': ['Beyond Live 1991 生命接触演唱会'],
    #    'title': ['再见理想'],
    #    'artist': ['BEYOND'],
    #    'genre': ['Blues']
    #   }
    metadata_dict = dict(metadata or {})
    metadata_dict = {k: v[0] for k, v in metadata_dict.items()}

    # Get title and artists name from filename when metadata is empty.
    if metadata is None:
        filename = os.path.split(fpath)[-1].split('.')[0]
        parts = filename.split(' - ', 1)
        if len(parts) == 2:
            title, artists_name = parts
            metadata_dict['artists_name'] = artists_name
        else:
            title = parts[0]
        metadata_dict['title'] = title
        metadata_dict['duration'] = 0
    else:
        # milesecond
        metadata_dict['duration'] = int(metadata.info.length * 1000)

    # Convert simplified to traditional, or reverse.
    if can_convert_chinese:
        metadata_dict = {k: convert_chinese(v, lang) for k, v in metadata_dict.items()}

    try:
        if fpath.endswith('flac'):
            data = FLACModel(**metadata_dict).dict()
            data['track'] = f"{data['track_number']}/{data['track_total']}"
            data['disc'] = f"{data['disc_number']}/{data['disc_total']}"
        elif fpath.endswith('ape'):
            data = APEModel(**metadata_dict).dict()
        else:
            data = EasyMP3Model(**metadata_dict).dict()
    except ValidationError:
        logger.exception(f'parse audio file metadata ({fpath}) failed')
        return
    return data


def gen_artist_name_list(artists_name, splitter, splitter_ignorance):
    # For example::
    # artists_name: 'Years & Years & Jess Glynne'
    # splitter: [',', '&']
    # splitter_ignorance: ['Years & Years']
    # return: ['Years & Years', 'Jess Glynne']
    if splitter_ignorance is None:
        splitter_ignorance = []
    if splitter_ignorance:
        artists_name = re.split(r'({})'.format('|'.join(splitter_ignorance)),
                                artists_name)
    else:
        artists_name = [artists_name]
    artist_name_list = []
    for artist_name in artists_name:
        if artist_name in splitter_ignorance:
            artist_name_list.append(artist_name)
        else:
            artist_name_list.extend(re.split(r'{}'.format('|'.join(splitter)),
                                             artist_name))
    return [artist_name.strip()
            for artist_name in artist_name_list if artist_name.strip()]


def add_song(fpath, g_songs, g_artists, g_albums, g_file_song, g_album_contributors,
             can_convert_chinese=False, lang='auto',
             delimiter='', expand_artist_songs=False,
             artist_splitter=[',', '&'], artist_splitter_ignorance=None,
             split_album_artist_name=False):
    """
    parse music file metadata with Easymp3 and return a song
    model.
    """
    data = read_audio_metadata(fpath, can_convert_chinese, lang)
    if data is None:
        return

    # NOTE: use {title}-{artists_name}-{album_name} as song identifier
    title = data['title']
    album_name = data['album_name']
    artist_name_list = gen_artist_name_list(
        data['artists_name'], artist_splitter, artist_splitter_ignorance)
    artists_name = ','.join(artist_name_list)
    duration = data['duration']
    album_artist_name = data['album_artist_name']

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
                         date=data['date'],
                         disc=data['disc'],
                         track=data['track'])
        g_file_song[fpath] = song_id
        g_songs[song_id] = song
    else:
        song = g_songs[song_id]
        logger.warning('Duplicate song: %s', fpath)
        return

    # 生成 album artist model
    if split_album_artist_name:
        album_artist_name_list = gen_artist_name_list(
            album_artist_name, artist_splitter, artist_splitter_ignorance)
    else:
        album_artist_name_list = [album_artist_name]

    album_artist_id_list, album_artist_list = [], []
    for artist_name in album_artist_name_list:
        artist_id = gen_id(artist_name)
        if artist_id not in g_artists:
            album_artist = create_artist(artist_id, artist_name)
            g_artists[artist_id] = album_artist
        else:
            album_artist = g_artists[artist_id]
        album_artist_id_list.append(artist_id)
        album_artist_list.append(album_artist)

    # 生成 album model
    album_id_str = delimiter.join([album_name, album_artist_name])
    album_id = gen_id(album_id_str)
    cover = gen_cover_url(song)
    if album_id not in g_albums:
        album = create_album(album_id, album_name, cover)
        g_albums[album_id] = album
        g_album_contributors[album_id] = []
    else:
        album = g_albums[album_id]

    # 处理专辑的歌手信息和歌曲信息，专辑歌手的专辑列表信息
    for album_artist in album_artist_list:
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
        if artist_id not in album_artist_id_list \
                and artist_id not in g_album_contributors[album_id]:
            g_album_contributors[album_id].append(artist_id)

    # 处理专辑歌手的歌曲信息: 有些作词人出合辑很少出现在歌曲歌手里(可选)
    for album_artist_ in album_artist_list:
        if expand_artist_songs and song not in album_artist_.hot_songs:
            album_artist_.hot_songs.append(song)


def scan_directory(directory, exts, depth=2):
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


def sort_album_func(album):
    if album.songs:
        return album.songs[0].date is not None, album.songs[0].date
    return False, '0'


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

        self._file_song = {}           # {fpath: song_id}
        self._song_file = {}           # {song_id: fpath}
        self._songs = {}               # {song_id: song}
        self._albums = {}              # {album_id: album)
        self._artists = {}             # {artist_id: artist)
        self._album_contributors = {}  # {album_id: [artist_id]}

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

    def remove(self, fpath):
        """add media file to database"""

    ############################

    def list_songs(self):
        return list(self._songs.values())

    def list_albums(self):
        return list(self._albums.values())

    def list_albums_by_contributor(self, artist_id):
        albums = []
        for album_id, artists in self._album_contributors.items():
            if artist_id in artists:
                album = self.get_album(album_id)
                albums.append(album)
        return albums

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

        is_cn_convert_enabled = can_convert_chinese()
        for fpath in media_files:
            add_song(fpath, self._songs, self._artists,
                     self._albums, self._file_song, self._album_contributors,
                     is_cn_convert_enabled, config.CORE_LANGUAGE,
                     config.IDENTIFIER_DELIMITER, config.EXPAND_ARTIST_SONGS,
                     config.ARTIST_SPLITTER, config.ARTIST_SPLITTER_IGNORANCE,
                     config.SPLIT_ALBUM_ARTIST_NAME)
        logger.info('录入本地音乐库完毕')

    def after_scan(self):
        # Sort the songs in a album.
        for album in self._albums.values():
            try:
                album.songs.sort(key=lambda x: (int(x.disc.split('/')[0]),
                                                int(x.track.split('/')[0])))
                if album.name != DEFAULT_ALBUM_NAME:
                    cover = gen_cover_url(album.songs[0])
                    album.cover = cover
            except:  # noqa
                logger.exception('Sort album songs failed.')

        # Select a pic_url for the artist
        for artist in self._artists.values():
            albums = []
            for album in self._albums.values():
                for artist_ in album.artists:
                    if artist_.identifier == artist.identifier:
                        albums.append(album)
                        continue
            if albums:
                albums.sort(key=sort_album_func, reverse=True)
                if albums:
                    artist.pic_url = albums[0].cover

            if not artist.pic_url and artist.hot_songs:
                # sort the artist hot_songs.
                artist.hot_songs.sort(key=lambda x: x.title)
                # Use a song's cover as artist cover.
                # https://github.com/feeluown/feeluown-local/pull/3/files#r362126996
                songs_with_unknown_album = [song for song in artist.hot_songs
                                            if song.album_name == DEFAULT_ALBUM_NAME]
                for song in sorted(songs_with_unknown_album,
                                   key=lambda x: (x.date != '', x.date),
                                   reverse=True):
                    artist.pic_url = gen_cover_url(song)
                    break

        # Cache the {song_id:fpath} mapping.
        self._song_file = {v: k for k, v in self._file_song.items()}
