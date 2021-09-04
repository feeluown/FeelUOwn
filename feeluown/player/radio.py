from collections import deque

from feeluown.library import ProviderFlags as PF


def calc_song_similarity(base, song):
    return 10


class SongRadio:
    def __init__(self, app, song):
        self._app = app
        self.root_song = song
        self._stack = deque([song])
        self._songs_set = set({})

    @classmethod
    def create(cls, app, song):
        if not app.library.check_flags_by_model(song, PF.similar):
            raise ValueError('the provider must support list similar song')
        return cls(app, song)

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
            songs = self._app.library.song_list_similar(song)
            for song in songs:
                if song not in self._songs_set:
                    valid_songs.append(song)

        # TODO: sort the songs by similarity
        for song in valid_songs:
            self._stack.append(song)
            self._songs_set.add(song)
        return valid_songs
