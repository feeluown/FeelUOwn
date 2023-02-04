# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
"""
TODO: 这个模块中目前逻辑非常多，包括音乐目录扫描、音乐库的构建等小部分，
这些小部分理论都可以从中拆除。
"""

import difflib
import logging
import re
import threading
from functools import wraps

from feeluown.excs import ProviderIOError

from feeluown.media import Media, Quality
from feeluown.library import AbstractProvider, ProviderV2, ModelType, SimpleSearchResult
from feeluown.utils.reader import create_reader
from feeluown.utils.utils import log_exectime
from feeluown.utils.audio import read_audio_cover
from .db import sort_album_func


logger = logging.getLogger(__name__)
SOURCE = 'local'


def wait_for_scan(func):
    """
    Some API of local provider can only return correct data after scan is finished.
    This decorator is designed to be used to decorate those API.
    """
    @wraps(func)
    def wrapper(this, *args, **kwargs):
        if not this._scan_finished.wait(timeout=1):
            raise ProviderIOError('scan is not still finished')
        return func(this, *args, **kwargs)
    return wrapper


class LocalProvider(AbstractProvider, ProviderV2):
    class meta:
        identifier = SOURCE
        name = '本地音乐'

    def __init__(self):
        super().__init__()

        self._app = None
        self._scan_finished = threading.Event()

        from .db import DB

        self.db = DB('')

    def initialize(self, app):
        self._app = app

    def handle_with_path(self, path, **_):
        """
        handle ('/songs/{identifier}/cover/data')
        """
        p = re.compile(r'/songs/(\S+)/cover/data')
        m = p.match(path)
        if m is not None:
            try:
                identifier = m.group(1)
            except IndexError:
                return None
            else:
                fpath = self.db.get_song_fpath(identifier)
                if fpath:
                    return read_audio_cover(fpath)[0]
        return None

    @property
    def identifier(self):
        return SOURCE

    @property
    def name(self):
        return '本地音乐'

    def scan(self, config, paths, depth=3):
        exts = config.MUSIC_FORMATS
        self.db.scan(config, paths, depth, exts)
        self.db.after_scan()
        self._scan_finished.set()

    def use_model_v2(self, model_type):
        return model_type in (ModelType.song, ModelType.album, ModelType.artist)

    @wait_for_scan
    def song_get(self, identifier):
        """implements SupportsSongGet protocol."""
        return self.db.get_song(identifier)

    def song_list_quality(self, _):
        """implements SupportsSongMultiQuality protocol."""
        return [Quality.Audio.sq]

    @wait_for_scan
    def song_get_media(self, song, _):
        """implements SupportsSongMultiQuality protocol."""
        fpath = self.db.get_song_fpath(song.identifier)
        if fpath:
            return Media(fpath)

    @wait_for_scan
    def album_get(self, identifier):
        """Implement SupportsAlbumGet protocol."""
        return self.db.get_album(identifier)

    @wait_for_scan
    def artist_get(self, identifier):
        """Implement SupportsArtistGet protocol."""
        return self.db.get_artist(identifier)

    @wait_for_scan
    def artist_create_songs_rd(self, artist):
        """Implement SupportsArtistSongsReader protocol."""
        artist = self.model_get(artist.meta.model_type, artist.identifier)
        return create_reader(artist.hot_songs)

    @wait_for_scan
    def artist_create_albums_rd(self, artist):
        """Implement SupportsArtistAlbumsReader protocol."""
        albums = []
        for album in self.db.list_albums():
            for artist_ in album.artists:
                if artist_.identifier == artist.identifier:
                    albums.append(album)
                    continue
        albums.sort(key=sort_album_func, reverse=True)
        return create_reader(albums)

    @wait_for_scan
    def artist_create_contributed_albums_rd(self, artist):
        albums = self.db.list_albums_by_contributor(artist.identifier)
        albums.sort(key=sort_album_func, reverse=True)
        return create_reader(albums)

    @property
    def songs(self):
        return self.db.list_songs()

    @property
    def albums(self):
        return self.db.list_albums()

    @property
    def artists(self):
        return self.db.list_artists()

    @log_exectime
    @wait_for_scan
    def search(self, keyword, **kwargs):
        from .db import to_brief_song

        limit = kwargs.get('limit', 10)
        repr_song_map = dict()
        for song in self.songs:
            key = song.title + ' ' + song.artists_name
            repr_song_map[key] = song
        choices = repr_song_map.keys()
        if choices:
            # TODO: maybe use a more reasonable algorithm.
            result = difflib.get_close_matches(keyword, choices, n=limit, cutoff=0)
        else:
            result = []
        result_songs = [repr_song_map[each] for each in result]

        return SimpleSearchResult(
            q=keyword,
            songs=[to_brief_song(song) for song in result_songs]
        )


provider = LocalProvider()
