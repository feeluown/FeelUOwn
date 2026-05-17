import logging
from numbers import Real
from feeluown.library import SongModel

logger = logging.getLogger(__name__)


class PreloadManager:
    def __init__(self, playlist):
        self._playlist = playlist
        self._preloading_song = None
        self._preloaded_song = None
        self._preloaded_media = None
        self._preloaded_metadata = None
        self._threshold_seconds = self._load_threshold_seconds()

    @property
    def threshold_seconds(self):
        return self._threshold_seconds

    def _load_threshold_seconds(self):
        try:
            cfg_threshold = (
                self._playlist._app.config.PREFETCH_PLAYLIST_THRESHOLD_SECONDS
            )
        except Exception:
            cfg_threshold = 30
        if not isinstance(cfg_threshold, Real):
            cfg_threshold = 30
        return float(cfg_threshold)

    def on_progress_changed(self, *args, **kwargs):
        self.maybe_preload_next_song(force=False)

    def on_song_changed(self, song):
        self.clear_state()

    def clear_state(self):
        self._preloading_song = None
        self._preloaded_song = None
        self._preloaded_media = None
        self._preloaded_metadata = None

    def consume_preloaded(self, song):
        if self._preloaded_song == song and self._preloaded_media is not None:
            media = self._preloaded_media
            metadata = self._preloaded_metadata
            self.clear_state()
            return media, metadata
        return None, None

    def maybe_preload_next_song(self, force: bool = False):
        if self._playlist.current_song is None:
            return

        if self._threshold_seconds <= 0:
            return

        next_song = self._playlist.next_song
        if next_song is None:
            return

        if self._preloaded_song is not None and self._preloaded_song != next_song:
            self.clear_state()

        if self._preloaded_song == next_song or self._preloading_song == next_song:
            return

        if not force:
            duration = getattr(self._playlist._app.player, "duration", None)
            position = getattr(self._playlist._app.player, "position", None)
            if not isinstance(duration, Real) or duration <= 0:
                return
            if not isinstance(position, Real) or position < 0:
                position = 0
            remaining = duration - position
            if remaining > self._threshold_seconds:
                return

        self._preloading_song = next_song
        self._playlist._app.task_mgr.run_afn_preemptive(
            self.preload_next_song,
            next_song,
            name="playlist.preload_media",
        )

    async def preload_next_song(self, song: SongModel):
        try:
            try:
                media = await self._playlist._prepare_media(song)
            except Exception:
                logger.exception("preload prepare_media failed")
                return

            if song != self._playlist.next_song:
                return

            if not media:
                return

            self._preloaded_song = song
            self._preloaded_media = media

            try:
                kwargs = {}
                if not self._playlist._app.has_gui:
                    kwargs["video"] = False
                self._playlist._app.player.queue_media(media, **kwargs)
            except Exception:
                logger.debug("queue next media into mpv failed", exc_info=True)

            try:
                self._preloaded_metadata = (
                    await self._playlist._metadata_mgr.prepare_for_song(song)
                )
            except Exception:
                self._preloaded_metadata = None
        finally:
            if self._preloading_song == song:
                self._preloading_song = None
