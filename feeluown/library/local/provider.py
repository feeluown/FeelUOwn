# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
"""
TODO: 这个模块中目前逻辑非常多，包括音乐目录扫描、音乐库的构建等小部分，
这些小部分理论都可以从中拆除。
"""

import logging
import os
import re

from fuzzywuzzy import process

from feeluown.media import Media, Quality
from feeluown.library import AbstractProvider, ProviderV2, ModelType, SimpleSearchResult
from feeluown.utils.reader import create_reader
from feeluown.utils.utils import log_exectime

from .utils import read_audio_cover

logger = logging.getLogger(__name__)
SOURCE = 'local'


class LocalProvider(AbstractProvider, ProviderV2):
    class meta:
        identifier = SOURCE
        name = '本地音乐'
        flags = {}

    def __init__(self):
        super().__init__()

        self._app = None

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

    def use_model_v2(self, model_type):
        return model_type in (ModelType.song, ModelType.album, ModelType.artist)

    def song_get(self, identifier):
        """implements SupportsSongGet protocol."""
        return self.db.get_song(identifier)

    def song_list_quality(self, _):
        """implements SupportsSongMultiQuality protocol."""
        return [Quality.Audio.sq]

    def song_get_media(self, song, _):
        """implements SupportsSongMultiQuality protocol."""
        fpath = self.db.get_song_fpath(song.identifier)
        if fpath:
            return Media(fpath)

    def album_get(self, identifier):
        """Implement SupportsAlbumGet protocol."""
        return self.db.get_album(identifier)

    def artist_get(self, identifier):
        """Implement SupportsArtistGet protocol."""
        return self.db.get_artist(identifier)

    def artist_create_songs_rd(self, artist):
        """Implement SupportsArtistSongsReader protocol."""
        artist = self.model_get(artist.meta.model_type, artist.identifier)
        return create_reader(artist.hot_songs)

    # TODO: list artist's contributed_albums
    def artist_create_albums_rd(self, artist):
        """Implement SupportsArtistAlbumsReader protocol."""
        albums = []
        for album in self.db.list_albums():
            for artist_ in album.artists:
                if artist_.identifier == artist.identifier:
                    albums.append(album)
                    continue
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
    def search(self, keyword, **kwargs):
        from .db import to_brief_song

        limit = kwargs.get('limit', 10)
        repr_song_map = dict()
        for song in self.songs:
            key = song.title + ' ' + song.artists_name
            repr_song_map[key] = song
        choices = repr_song_map.keys()
        if choices:
            result = process.extract(keyword, choices, limit=limit)
        else:
            result = []
        result_songs = []
        for each, score in result:
            # if score > 80, keyword is almost included in song key
            if score > 80:
                result_songs.append(repr_song_map[each])
        return SimpleSearchResult(
            q=keyword,
            songs=[to_brief_song(song) for song in result_songs]
        )

    def song_get_lyric(self, song):
        return None


provider = LocalProvider()
