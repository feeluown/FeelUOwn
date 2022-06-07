from feeluown.library import ModelType
from feeluown.utils.utils import DedupList


class RecentlyPlayed:
    """
    RecentlyPlayed records recently played models, currently including songs
    and videos. Maybe artists and albums will be recorded in the future.
    """
    def __init__(self, playlist):
        # Store recently played songs. Newest song is appended to left.
        self._songs = DedupList()

        playlist.song_changed_v2.connect(self._on_song_played)

    def init_from_models(self, models):
        for model in models:
            if ModelType(model.meta.model_type) is ModelType.song:
                self._songs.append(model)

    def list_songs(self):
        """List recently played songs (list of BriefSongModel).
        """
        return list(self._songs.copy())

    def _on_song_played(self, song, _):
        # Remove the song and place the song at the very first if it already exists.
        if song is None:
            return
        if song in self._songs:
            self._songs.remove(song)
        if len(self._songs) >= 100:
            self._songs.pop()
        self._songs.insert(0, song)
