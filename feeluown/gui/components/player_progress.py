from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout

from feeluown.gui.widgets.labels import ProgressLabel, DurationLabel
from feeluown.gui.widgets.progress_slider import ProgressSlider

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class PlayerProgressRatioLabel(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)

        self._app = app

        self.duration_label = DurationLabel(app, parent=self)
        self.progress_label = ProgressLabel(app, parent=self)

        font = self.font()
        font.setPixelSize(10)
        for label in (self.duration_label, self.progress_label):
            label.setFont(font)
            label.setMinimumWidth(26)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self._layout.addWidget(self.progress_label)
        self._layout.addWidget(QLabel('/'))
        self._layout.addWidget(self.duration_label)


class PlayerProgressSliderAndLabel(QWidget):
    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)

        self._app = app
        self.slider = ProgressSlider(app, parent=self)
        self.label = PlayerProgressRatioLabel(app, parent=self)

        self._layout = QHBoxLayout(self)
        self._layout.addWidget(self.slider)
        self._layout.addWidget(self.label)
