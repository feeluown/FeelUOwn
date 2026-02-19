import warnings
from typing import Optional

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPainter, QImage
from PyQt6.QtWidgets import QLabel, QSizePolicy, QMenu

from feeluown.i18n import t
from feeluown.library import SupportsImgUrlToMedia
from feeluown.media import Media, MediaType
from feeluown.gui.drawers import PixmapDrawer
from feeluown.gui.image import open_image


class CoverLabel(QLabel):
    def __init__(self, parent=None, pixmap=None, radius=3):
        super().__init__(parent=parent)

        self._radius = radius
        self.drawer = PixmapDrawer(None, self, self._radius)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding
        )

    def show_pixmap(self, pixmap):
        """
        .. versiondeprecated:: 3.8.11
        """
        warnings.warn("You should use show_img", DeprecationWarning)
        self.updateGeometry()
        self.update()  # Schedule a repaint to refresh the UI ASAP.

    def show_img(self, img: Optional[QImage]):
        if not img or img.isNull():
            self.drawer = PixmapDrawer(None, self, self._radius)
        else:
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
        painter = QPainter(self)
        self.drawer.draw(painter)

    def contextMenuEvent(self, e):
        if self.drawer.get_img() is None:
            return
        menu = QMenu()
        action = menu.addAction(t("show-original-image"))
        action.triggered.connect(lambda: open_image(self.drawer.get_img()))
        menu.exec(e.globalPos())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.updateGeometry()

    def sizeHint(self):
        super_size = super().sizeHint()
        pixmap = self.drawer.get_pixmap()
        if pixmap is None:
            return super_size
        h = (self.width() * pixmap.height()) // pixmap.width()
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

    async def show_cover_media(self, cover_media: Optional[Media], cover_uid):
        if cover_media is None:
            self.show_img(None)
            return
        content = await self._app.img_mgr.get(cover_media, cover_uid)
        img = QImage()
        img.loadFromData(content)
        self.show_img(img)

    async def show_cover(self, cover, cover_uid):
        # Backward-compatible API. Prefer show_cover_media when caller can
        # provide a provider-aware Media object.
        if isinstance(cover, Media):
            cover_media = cover
        elif isinstance(cover, str):
            cover_media = Media(cover, MediaType.image)
        else:
            raise TypeError(f"unsupported cover type: {type(cover)!r}")
        await self.show_cover_media(cover_media, cover_uid)

    async def show_cover_with_source(
        self, artwork: str, source: str, cover_uid: str
    ):
        if not artwork:
            self.show_img(None)
            return
        provider = self._app.library.get(source) if source else None
        if isinstance(provider, SupportsImgUrlToMedia):
            cover_media = provider.img_url_to_media(artwork)
        else:
            cover_media = Media(artwork, MediaType.image)
        await self.show_cover_media(cover_media, cover_uid)


if __name__ == "__main__":
    from feeluown.gui.debug import simple_layout

    with simple_layout() as layout:
        label = CoverLabel()
        layout.addWidget(label)
        label.resize(100, 100)
        label.show_img(QImage("/path/to/test.png"))
