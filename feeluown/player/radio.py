from collections import deque
from typing import TYPE_CHECKING, List

from feeluown.library import SupportsSongSimilar, BriefSongModel

if TYPE_CHECKING:
    from feeluown.app import App


class Radio:
    def __init__(self, app: 'App', songs: List[BriefSongModel]):
        self._app = app
        self._stack = deque(songs)
        # B is a similar song of A. Also, A may be a similar song of B.
        # The songs_set store all songs to avoid fetching duplicate songs.
        self._songs_set = set(songs)

    def fetch_songs_func(self, number):
        """implement fm.fetch_songs_func

        TODO: We have to design a better similar-song-finding algorithm and
        we should adjust the similarity of a song by user feedback.

        Currently, we have the following ways
        1. similar songs (most providers have this functionality)
        2. a random song in the same album or similar album
        3. popular songs sang by the same artist or similar artist
        """

        valid_songs = []

        # fetch at least $number similar songs
        while len(valid_songs) < number:
            if not self._stack:
                break
            song = self._stack.popleft()
            # User can mark a song as 'dislike' by removing it from playlist.
            if song not in self._app.playlist.list():
                continue
            provider = self._app.library.get(song.source)
            # Provider is ensured to SupportsSongsimilar during creating.
            if not isinstance(provider, SupportsSongSimilar):
                continue
            songs = provider.song_list_similar(song)
            for song in songs:
                if song not in self._songs_set:
                    valid_songs.append(song)

        # TODO: sort the songs by similarity
        for song in valid_songs:
            self._stack.append(song)
            self._songs_set.add(song)
        return valid_songs


class SongRadio:
    """SongRadio recommend songs based on a song."""

    def __init__(self, app: 'App', song):
        self._app = app
        self.root_song = song
        self._radio = Radio(app, [song])

    @classmethod
    def create(cls, app, song):
        provider = app.library.get(song.source)
        if provider is not None and isinstance(provider, SupportsSongSimilar):
            return cls(app, song)
        raise ValueError('the provider must support list similar song')

    def fetch_songs_func(self, number):
        return self._radio.fetch_songs_func(number)


class SongsRadio:
    def __init__(self, app: 'App', songs: List[BriefSongModel]):
        self._app = app
        self._radio = Radio(self._app, songs)

    def fetch_songs_func(self, number):
        return self._radio.fetch_songs_func(number)
