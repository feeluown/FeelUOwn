from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPainter, QPalette
from PyQt5.QtWidgets import QAbstractSlider

from feeluown.gui.drawers import VolumeIconDrawer
from feeluown.gui.helpers import painter_save, darker_or_lighter


class VolumeButton(QAbstractSlider):
    change_volume_needed = pyqtSignal([int])

    def __init__(self, length=30, padding=0.25, parent=None):
        super().__init__(parent=parent)

        self.setToolTip('调整音量')

        font = self.font()
        font.setPixelSize(length // 3)
        self.setFont(font)

        self.__pressed = False
        self.__checked = False

        self.setMinimum(0)
        self.setMaximum(100)

        padding = int(length * padding if padding < 1 else padding)
        self.drawer = VolumeIconDrawer(length, padding)
        self.valueChanged.connect(self.change_volume_needed.emit)
        self.setFixedSize(length, length)

    def on_volume_changed(self, value):
        # blockSignals to avoid circular setVolume.
        # https://stackoverflow.com/a/4146392/4302892
        self.blockSignals(True)
        self.setValue(value)
        self.drawer.set_volume(value)
        self.blockSignals(False)
        self.update()

    def paintEvent(self, _) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.__checked is True:
            with painter_save(painter):
                painter.setPen(Qt.NoPen)
                color = self.palette().color(QPalette.Background)
                painter.setBrush(darker_or_lighter(color, 120))
                painter.drawEllipse(self.rect())
            painter.drawText(self.rect(), Qt.AlignCenter, f'{self.value()}%')
        else:
            self.drawer.draw(painter, self.palette())

    def mousePressEvent(self, e) -> None:
        super().mousePressEvent(e)
        if e.button() == Qt.LeftButton:
            self.__pressed = True

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if e.button() == Qt.LeftButton:
            if self.__pressed is True:
                self.__pressed = False
                self.__checked = not self.__checked
                # schedule an update to refresh ASAP.
                self.update()


if __name__ == '__main__':
    from feeluown.gui.debug import simple_layout

    with simple_layout() as layout:
        layout.addWidget(VolumeButton(100))
