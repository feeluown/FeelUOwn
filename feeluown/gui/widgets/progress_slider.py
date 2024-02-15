from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSlider, QAbstractSlider

from feeluown.player import State
from feeluown.gui.helpers import IS_MACOS


class DraggingContext:
    def __init__(self):
        self.is_media_changed = False


class ProgressSlider(QSlider):

    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self._dragging_ctx: Optional[DraggingContext] = None

        self.setToolTip('拖动调节进度')
        self.setRange(0, 0)  # User can't drag the slider control when range is empty.
        self.setOrientation(Qt.Horizontal)

        self.sliderPressed.connect(self.on_pressed)
        self.sliderReleased.connect(self.on_released)
        self.actionTriggered.connect(self.on_action_triggered)

        self._app.player.duration_changed.connect(self.update_total, aioqueue=True)
        self._app.player_pos_per300ms.changed.connect(self.update_progress)
        self._app.player.media_changed.connect(self.on_media_changed)

        if IS_MACOS:
            self.setMinimumHeight(25)  # otherwise, the handler can't show properly

    def update_total(self, s):
        s = s or 0
        self.setRange(0, int(s))

    def update_progress(self, s):
        # Only update progress when it is not dragging.
        if not self.is_dragging:
            s = s or 0
            self.setValue(int(s))

    @property
    def is_dragging(self):
        return self._dragging_ctx is not None

    def on_pressed(self):
        self._dragging_ctx = DraggingContext()
        if self._app.player.state is State.playing:
            self._app.player.pause()

    def on_released(self):
        # Only set position if the player has a valid media and the media is changed.
        assert self._dragging_ctx is not None
        if not self._dragging_ctx.is_media_changed:
            self.maybe_update_player_position(self.value())
        self._dragging_ctx = None

        # Update progress after dragging.
        self.update_progress(self._app.player.position)

    def on_media_changed(self, media):
        if self._dragging_ctx is not None:
            self._dragging_ctx.is_media_changed = True

    def on_action_triggered(self, action):
        # SliderMove is handled seperately. Just ignore it.
        if action not in (QAbstractSlider.SliderNoAction, QAbstractSlider.SliderMove):
            slider_position = self.sliderPosition()
            self.maybe_update_player_position(slider_position)

    def maybe_update_player_position(self, position):
        if self._app.player.current_media:
            self._app.player.position = position
            # No matter if the player is paused/stopped before dragging,
            # we resume the player. Bilibili web player did the same.
            self._app.player.resume()
