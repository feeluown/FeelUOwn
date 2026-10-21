# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
"""
TODO: The current logic in this module is very extensive,
including small parts such as music directory scanning and music library construction;
in theory, all these small parts can be extracted from it.
"""

import difflib
import logging
import re
import threading
from functools import wraps

from feeluown.excs import ProviderIOError

from feeluown.i18n import t
from feeluown.media import Media, MediaType, Quality
from feeluown.library import (
    AbstractProvider, BriefVideoModel, ModelType, ProviderV2, SearchType,
    SimpleSearchResult, VideoModel,
)
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
        name = t('local-tracks')

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
        return LocalProvider.meta.name

    def scan(self, config, paths, depth=3):
        exts = config.MUSIC_FORMATS
        self.db.scan(config, paths, depth, exts)
        self.db.after_scan()
        self._scan_finished.set()

    def use_model_v2(self, model_type):
        return model_type in (ModelType.song, ModelType.album, ModelType.artist,
                              ModelType.video)

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
    def video_get(self, identifier):
        song = self.db.get_video(identifier)
        if song is None:
            return None
        from .db import gen_cover_url

        album = self.db.get_album(song.album.identifier) if song.album else None
        return VideoModel(
            identifier=song.identifier,
            source=SOURCE,
            title=song.title,
            artists=song.artists,
            duration=song.duration,
            cover=album.cover if album and album.cover else gen_cover_url(song),
            released=song.date[:10],
        )

    def video_list_quality(self, _):
        return [Quality.Video.sd]

    @wait_for_scan
    def video_get_media(self, video, _):
        fpath = self.db.get_song_fpath(video.identifier)
        if fpath and self.db.get_video(video.identifier) is not None:
            return Media(fpath, MediaType.video)

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
    def videos(self):
        return self.db.list_videos()

    @property
    def artists(self):
        return self.db.list_artists()

    @log_exectime
    @wait_for_scan
    def search(self, keyword, **kwargs):
        from .db import to_brief_album, to_brief_artist, to_brief_song

        limit = kwargs.get('limit', 10)
        search_type = SearchType.parse(kwargs.get('type_') or SearchType.so)
        if search_type is SearchType.so:
            models = self.songs
            key_for = lambda song: song.title + ' ' + song.artists_name
        elif search_type is SearchType.al:
            models = self.albums
            key_for = lambda album: album.name + ' ' + album.artists_name
        elif search_type is SearchType.ar:
            models = self.artists
            key_for = lambda artist: artist.name
        elif search_type is SearchType.vi:
            models = self.videos
            key_for = lambda video: video.title + ' ' + video.artists_name
        else:
            return SimpleSearchResult(q=keyword, source=SOURCE)

        model_map = {key_for(model): model for model in models}
        choices = model_map.keys()
        if choices:
            # TODO: maybe use a more reasonable algorithm.
            result = difflib.get_close_matches(keyword, choices, n=limit, cutoff=0)
        else:
            result = []
        matches = [model_map[each] for each in result]

        if search_type is SearchType.so:
            return SimpleSearchResult(q=keyword, source=SOURCE,
                                      songs=[to_brief_song(song) for song in matches])
        if search_type is SearchType.al:
            return SimpleSearchResult(q=keyword, source=SOURCE,
                                      albums=[to_brief_album(album) for album in matches])
        if search_type is SearchType.ar:
            return SimpleSearchResult(q=keyword, source=SOURCE,
                                      artists=[to_brief_artist(artist) for artist in matches])
        return SimpleSearchResult(
            q=keyword,
            source=SOURCE,
            videos=[BriefVideoModel(
                identifier=video.identifier, source=SOURCE, title=video.title,
                artists_name=video.artists_name, duration_ms=video.duration_ms,
            ) for video in matches],
        )


provider = LocalProvider()
