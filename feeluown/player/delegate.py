import asyncio

from feeluown.utils import aio
from feeluown.utils.dispatch import Signal
from .base_player import AbstractPlayer, State


class PlayerPositionDelegate:
    """
    Player notify others through signal when properties are changed. Mpvplayer
    emit signal in non-main thread, and some receivers need to run in main thread.
    From the profile result(#669), we can see that the cross-thread communication
    costs a lot of CPU resources. When the signal emits too frequently, it
    causes obvious performance degration.

    This delegate runs in main thread, so the issue is almost solved. In addition,
    it emits position_changed signals with lower frequency by default.

    .. versionadded:: 3.8.11
        This class is *experimental*.
    """
    def __init__(self, player: AbstractPlayer, interval=300):
        self._position: float = player.position  # seconds
        self._interval = interval  # microseconds
        self._interval_s = interval / 1000  # seconds

        self._player = player
        self._player.seeked.connect(self._update_position_and_emit)
        self._player.state_changed.connect(self.on_state_changed, aioqueue=True)
        self._player.media_changed.connect(self._update_position_and_emit)

        self.changed = Signal()
        self._should_stop = False

    def initialize(self):
        aio.run_afn(self.start)

    async def start(self):
        while not self._should_stop:
            await asyncio.sleep(self._interval_s)
            self._update_position_and_emit()

    def stop(self):
        self._should_stop = True

    def on_state_changed(self, state):
        # When state is changed, update immediately.
        if state == State.playing:
            self._update_position_and_emit()

    def _update_position_and_emit(self, *_):
        self._position = self._player.position
        self.changed.emit(self._position)
