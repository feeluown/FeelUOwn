from PyQt6.QtCore import QRect
from PyQt6.QtGui import QImage, QPainter

from feeluown.gui.drawers import SizedPixmapDrawer


def test_sized_pixmap_drawer_uses_placeholder_for_null_image(qapp):
    drawer = SizedPixmapDrawer(QImage(), QRect(0, 0, 20, 20))
    canvas = QImage(20, 20, QImage.Format.Format_ARGB32)
    painter = QPainter(canvas)

    try:
        drawer.draw(painter)
    finally:
        painter.end()

    assert drawer.get_img() is None
    assert drawer.get_pixmap() is None
