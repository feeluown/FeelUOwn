from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSlider

from feeluown.app import App


class VolumeSlider(QSlider):
    def __init__(self, app: App, parent=None):
        super().__init__(parent)

        self._app = app
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(100)
        self.sliderMoved.connect(self.on_slider_moved)
        self.setOrientation(Qt.Horizontal)

    def on_slider_moved(self, value):
        self._app.player.volume = value
