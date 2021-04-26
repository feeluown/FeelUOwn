from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QPainter, QBrush, QImage, QPixmap
from PyQt5.QtWidgets import QLabel, QSizePolicy


class CoverLabel(QLabel):
    def __init__(self, parent=None, pixmap=None):
        super().__init__(parent=parent)

        self._pixmap = pixmap
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

    def show_pixmap(self, pixmap):
        self._pixmap = pixmap
        self.updateGeometry()

    def paintEvent(self, e):
        """
        draw pixmap with border radius

        We found two way to draw pixmap with border radius,
        one is as follow, the other way is using bitmap mask,
        but in our practice, the mask way has poor render effects
        """
        if self._pixmap is None:
            return
        radius = 3
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        scaled_pixmap = self._pixmap.scaledToWidth(
            self.width(),
            mode=Qt.SmoothTransformation
        )
        size = scaled_pixmap.size()
        brush = QBrush(scaled_pixmap)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        y = (size.height() - self.height()) // 2
        painter.save()
        painter.translate(0, -y)
        rect = QRect(0, y, self.width(), self.height())
        painter.drawRoundedRect(rect, radius, radius)
        painter.restore()
        painter.end()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.updateGeometry()

    def sizeHint(self):
        super_size = super().sizeHint()
        if self._pixmap is None:
            return super_size
        h = (self.width() * self._pixmap.height()) // self._pixmap.width()
        # cover label height hint can be as large as possible, since the
        # parent width has been set maximumHeigh
        w = self.width()
        return QSize(w, min(w, h))


class CoverLabelV2(CoverLabel):
    """

    .. versionadded:: 3.7.8
    """
    def __init__(self, app):
        super().__init__(parent=None)

        self._app = app

    async def show_cover(self, url, cover_uid):
        content = await self._app.img_mgr.get(url, cover_uid)
        img = QImage()
        img.loadFromData(content)
        pixmap = QPixmap(img)
        if not pixmap.isNull():
            self.show_pixmap(pixmap)
