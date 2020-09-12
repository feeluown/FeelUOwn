from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSlider


class ProgressSlider(QSlider):

    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self._draging = False

        self.setToolTip('拖动调节进度')

        self.setOrientation(Qt.Horizontal)
        self.sliderPressed.connect(self._on_pressed)
        self.sliderReleased.connect(self._on_released)

        self._app.player.duration_changed.connect(
            self.set_duration, aioqueue=True)
        self._app.player.position_changed.connect(
            self.update_state, aioqueue=True)

    def _on_pressed(self):
        self._draging = True
        self._app.player.pause()

    def _on_released(self):
        self._draging = False
        self._app.player.position = self.value()
        self._app.player.resume()

    def set_duration(self, s):
        if not self._draging:
            if s is not None:
                self.setRange(0, s)

    def update_state(self, s):
        if not self._draging:
            if s is None:
                s = 0
            self.setValue(s)
