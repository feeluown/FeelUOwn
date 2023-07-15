import warnings

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPainter, QImage
from PyQt5.QtWidgets import QLabel, QSizePolicy, QMenu

from feeluown.gui.drawers import PixmapDrawer
from feeluown.gui.image import open_image


class CoverLabel(QLabel):
    def __init__(self, parent=None, pixmap=None, radius=3):
        super().__init__(parent=parent)

        self._radius = radius
        self.drawer = None
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

    def show_pixmap(self, pixmap):
        """
        .. versiondeprecated:: 3.8.11
        """
        warnings.warn('You should use show_img', DeprecationWarning)
        self.updateGeometry()
        self.update()  # Schedule a repaint to refresh the UI ASAP.

    def show_img(self, img: QImage):
        if not img or img.isNull():
            self.drawer = None
            return

        self.drawer = PixmapDrawer(img, self, self._radius)
        self.updateGeometry()
        self.update()

    def paintEvent(self, e):
        """
        draw pixmap with border radius

        We found two way to draw pixmap with border radius,
        one is as follow, the other way is using bitmap mask,
        but in our practice, the mask way has poor render effects
        """
        if self.drawer:
            painter = QPainter(self)
            self.drawer.draw(painter)

    def contextMenuEvent(self, e):
        if self.drawer is None:
            return
        menu = QMenu()
        action = menu.addAction('查看原图')
        action.triggered.connect(
            lambda: open_image(self.drawer.get_img()))  # type: ignore
        menu.exec(e.globalPos())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.updateGeometry()

    def sizeHint(self):
        super_size = super().sizeHint()
        if self.drawer is None:
            return super_size
        h = (self.width() * self.drawer.get_pixmap().height()) \
            // self.drawer.get_pixmap().width()
        # cover label height hint can be as large as possible, since the
        # parent width has been set maximumHeigh
        w = self.width()
        return QSize(w, min(w, h))


class CoverLabelV2(CoverLabel):
    """

    .. versionadded:: 3.7.8
    """
    def __init__(self, app, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)

        self._app = app

    async def show_cover(self, url, cover_uid):
        content = await self._app.img_mgr.get(url, cover_uid)
        img = QImage()
        img.loadFromData(content)
        self.show_img(img)
