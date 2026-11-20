import time
from typing import Dict, List, Tuple

from feeluown.library import ModelType, reverse
from feeluown.utils.utils import DedupList


class RecentlyPlayed:
    """
    RecentlyPlayed records recently played models, currently including songs
    and videos. Maybe artists and albums will be recorded in the future.

    In addition to the recent song list, it keeps a bounded play history
    with timestamps so that smart playlists can evaluate rules such as
    most-played or recently-played-in-last-N-days.
    """

    MAX_SONGS = 100
    MAX_HISTORY = 2000

    def __init__(self, playlist):
        # Store recently played songs. Newest song is appended to left.
        self._songs = DedupList()
        # Play history in chronological order: list of (uri, song_line, timestamp).
        # uri is the stable key (fuo://...), song_line keeps display fields
        # so it can be resolved after restart.
        self._history: List[Tuple[str, str, float]] = []
        # Latest model instance for each uri.
        self._models: Dict[str, object] = {}

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
        self.record_play(song, timestamp=None)

    def record_play(self, song, timestamp=None):
        """Record one play event.

        This is the single place that updates songs/history/models so that
        tests and future callers share the same behavior.
        """
        if song is None:
            return
        if ModelType(song.meta.model_type) is not ModelType.song:
            return
        if song in self._songs:
            self._songs.remove(song)
        if len(self._songs) >= self.MAX_SONGS:
            self._songs.pop()
        self._songs.insert(0, song)

        try:
            uri = reverse(song)
        except Exception:
            return
        try:
            song_line = reverse(song, as_line=True)
        except Exception:
            song_line = uri
        now = timestamp if timestamp is not None else time.time()
        self._models[uri] = song
        self._history.append((uri, song_line, now))
        # Keep history bounded: drop oldest entries first.
        overflow = len(self._history) - self.MAX_HISTORY
        if overflow > 0:
            del self._history[0:overflow]

    def _cutoff(self, time_range_days, now=None):
        if time_range_days is None:
            return None
        now = now if now is not None else time.time()
        return now - time_range_days * 86400

    def get_play_counts(self, time_range_days=None, now=None):
        """Return {uri: play_count}, optionally filtered by time range."""
        cutoff = self._cutoff(time_range_days, now=now)
        counts: Dict[str, int] = {}
        for uri, _, ts in self._history:
            if cutoff is not None and ts < cutoff:
                continue
            counts[uri] = counts.get(uri, 0) + 1
        return counts

    def get_last_played_map(self, time_range_days=None, now=None):
        """Return {uri: last_played_timestamp}."""
        cutoff = self._cutoff(time_range_days, now=now)
        last: Dict[str, float] = {}
        for uri, _, ts in self._history:
            if cutoff is not None and ts < cutoff:
                continue
            if uri not in last or ts > last[uri]:
                last[uri] = ts
        return last

    def get_first_seen_map(self):
        """Return {uri: first_seen_timestamp} over the whole history."""
        first: Dict[str, float] = {}
        for uri, _, ts in self._history:
            if uri not in first or ts < first[uri]:
                first[uri] = ts
        return first

    def get_models_map(self):
        """Return {uri: latest_model}."""
        return dict(self._models)

    def get_most_played(self, limit=50, time_range_days=None, now=None,
                        min_play_count=1, sources=None):
        """Return most played song models, sorted by count then recency."""
        counts = self.get_play_counts(time_range_days, now=now)
        last_map = self.get_last_played_map(time_range_days, now=now)
        items = []
        for uri, model in self._models.items():
            if sources is not None and getattr(model, 'source', None) not in sources:
                continue
            if time_range_days is not None and uri not in last_map:
                continue
            count = counts.get(uri, 0)
            if count < min_play_count:
                continue
            items.append((uri, model, count, last_map.get(uri, 0)))
        items.sort(key=lambda t: (-t[2], -t[3]))
        return [model for _, model, _, _ in items[:limit]]

    def get_recently_played_in_range(self, limit=50, time_range_days=None, now=None,
                                     sources=None):
        """Return songs sorted by last played time, optionally in range."""
        last_map = self.get_last_played_map(time_range_days, now=now)
        items = []
        for uri, model in self._models.items():
            if sources is not None and getattr(model, 'source', None) not in sources:
                continue
            if uri not in last_map:
                continue
            items.append((model, last_map[uri]))
        items.sort(key=lambda t: -t[1])
        return [model for model, _ in items[:limit]]

    def get_state(self):
        """Return serializable play history for App.dump_state."""
        return [
            {'song': song_line, 'timestamp': ts}
            for _, song_line, ts in self._history
        ]

    def load_state(self, items):
        """Load play history dumped by get_state.

        Each item is {'song': line, 'timestamp': ts}. Invalid lines are skipped.
        """
        from feeluown.library import resolve, ResolverNotFound, ResolveFailed

        self._history.clear()
        self._models.clear()
        self._songs.clear()
        for item in items:
            if isinstance(item, str):
                # Backward compat: plain uri line without timestamp.
                line, ts = item, time.time()
            else:
                line, ts = item.get('song'), item.get('timestamp', time.time())
            if not line:
                continue
            try:
                model = resolve(line)
            except (ResolverNotFound, ResolveFailed, Exception):
                continue
            if ModelType(model.meta.model_type) is not ModelType.song:
                continue
            try:
                uri = reverse(model)
            except Exception:
                continue
            self._models[uri] = model
            self._history.append((uri, line, float(ts)))
        # Rebuild recent songs list: newest first, dedup, bounded.
        seen = set()
        for uri, line, _ in reversed(self._history):
            if uri in seen:
                continue
            seen.add(uri)
            model = self._models.get(uri)
            if model is not None:
                self._songs.append(model)
        # _songs is newest-first; trim oldest (tail) on overflow.
        while len(self._songs) > self.MAX_SONGS:
            self._songs.pop()
        overflow = len(self._history) - self.MAX_HISTORY
        if overflow > 0:
            del self._history[0:overflow]
