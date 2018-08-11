from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import (
    QSlider,
    QPushButton,
    QStyle,
)


class VolumeSlider(QSlider):

    def __init__(self, parent=None, initial_value=100):
        super().__init__(parent)

        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(initial_value)
        self.setWindowFlags(Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def is_mute(self):
        return self.value() <= 0

    def showEvent(self, event):
        parent = self.parent()
        if parent:
            pgeom = parent.geometry()
            geom = self.geometry()
            if self.orientation() == Qt.Horizontal:
                x = pgeom.width() + 2
                y = (pgeom.height() - geom.height())//2
            else:
                x = (pgeom.width() - geom.width())//2
                y = -geom.height() - 2
            point = QPoint(x, y)
            self.move(parent.mapToGlobal(point))

    def mouseReleaseEvent(self, event):
        if self.rect().contains(event.pos()):
            value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(),
                                                   event.x(), self.width())
            self.setValue(value)
        else:
            self.close()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.isVisible():
            self.close()

    def leaveEvent(self, event):
        self.close()


class VolumeButton(QPushButton):
    UNMUTED_ICON = 0
    MUTED_ICON = 1

    def __init__(self, parent=None, *, vertical=True, icons=None):
        super().__init__(parent)
        self.setMaximumWidth(40)
        self.icons = icons
        if self.icons:
            self.icon = VolumeButton.UNMUTED_ICON
            self.setIcon(self.icons['unmuted'])

        self.slider = VolumeSlider(self)
        if vertical:
            self.slider.setOrientation(Qt.Vertical)
        self.slider.valueChanged.connect(self.change_icon)
        self.clicked.connect(self.slider.show)

    def change_icon(self):
        if not self.icons:
            return
        if self.slider.is_mute():
            self.setIcon(self.icons['muted'])
            self.icon = VolumeButton.MUTED_ICON
        elif self.icon == VolumeButton.MUTED_ICON:
            self.setIcon(self.icons['unmuted'])
            self.icon = VolumeButton.UNMUTED_ICON

    def connect(self, func):
        self.slider.valueChanged.connect(func)
