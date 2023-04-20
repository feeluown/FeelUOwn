import warnings

from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QPainter, QBrush, QImage, QPixmap
from PyQt5.QtWidgets import QLabel, QSizePolicy, QMenu

from feeluown.gui.image import open_image


class CoverLabel(QLabel):
    def __init__(self, parent=None, pixmap=None):
        super().__init__(parent=parent)

        # There is possibility that self._img is None and self._pixmap is not None.
        # When self._img is not None, self._pixmap can not be None.
        self._img = None
        self._pixmap = pixmap
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

    def show_pixmap(self, pixmap):
        """
        .. versiondeprecated:: 3.8.11
        """
        warnings.warn('You should use show_img', DeprecationWarning)
        self._img = None
        self._pixmap = pixmap
        self.updateGeometry()
        self.update()  # Schedule a repaint to refresh the UI ASAP.

    def show_img(self, img: QImage):
        if img.isNull():
            return

        self._img = img
        new_img = img.scaledToWidth(self.width())
        pixmap = QPixmap(new_img)
        self._pixmap = pixmap
        self.updateGeometry()
        self.update()

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
        size = self._pixmap.size()
        brush = QBrush(self._pixmap)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        y = (size.height() - self.height()) // 2
        painter.save()
        painter.translate(0, -y)
        rect = QRect(0, y, self.width(), self.height())
        painter.drawRoundedRect(rect, radius, radius)
        painter.restore()
        painter.end()

    def contextMenuEvent(self, e):
        if self._img is None:
            return
        menu = QMenu()
        action = menu.addAction('查看原图')
        action.triggered.connect(lambda: open_image(self._img))
        menu.exec(e.globalPos())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.updateGeometry()

        if self._img is not None:
            # Resize pixmap.
            img = self._img.scaledToWidth(self.width(), Qt.SmoothTransformation)
            self._pixmap = QPixmap(img)
        elif self._pixmap is not None:
            self._pixmap = self._pixmap.scaledToWidth(
                self.width(),
                mode=Qt.SmoothTransformation
            )

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
        self.show_img(img)
