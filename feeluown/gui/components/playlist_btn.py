from typing import TYPE_CHECKING

from PyQt5.QtGui import QPainter, QPolygonF, QColor, QTextOption
from PyQt5.QtCore import QPointF, QRectF, Qt

from feeluown.player import PlaylistMode
from feeluown.gui.widgets import SelfPaintAbstractSquareButton
from feeluown.gui.helpers import SOLARIZED_COLORS

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class PlaylistButton(SelfPaintAbstractSquareButton):
    def __init__(self, app: 'GuiApp', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app

        self.setToolTip('显示当前播放列表')
        # PlaylistButton show FM text on the button when FM mode is actiavted,
        # so update the button when mode is changed.
        self._app.playlist.mode_changed.connect(lambda *args: self.update(), weak=False)
        self.clicked.connect(self.raise_playlist_view)

    def raise_playlist_view(self, *_):
        playlist_overlay = self._app.ui.playlist_overlay

        if not playlist_overlay.isVisible():
            width = max(self._app.width() // 4, 330)
            x = self._app.width() - width
            height = self._app.height()
            playlist_overlay.setGeometry(x, 0, width, height)
            playlist_overlay.show()
            playlist_overlay.setFocus()
            # Put the widget on top.
            playlist_overlay.raise_()

    def paintEvent(self, e):
        # pylint: disable=too-many-locals
        width = height = self.width() - self._padding * 2
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        self.paint_round_bg_when_hover(painter)

        painter.save()
        painter.translate((self.width() - width) // 2, (self.height() - height) // 2)

        line_height = 1.3
        line_margin = (height - 3 * line_height) / 3
        h1 = line_margin
        h2 = h1 + line_margin + line_height
        h3 = h2 + line_margin + line_height

        pen = painter.pen()
        pen.setWidthF(line_height)
        painter.setPen(pen)
        painter.setBrush(pen.color())

        # Draw triangle and first line
        triangle_side_length_half = line_margin * 0.6
        triangle_height = triangle_side_length_half * 1.7
        triangle = QPolygonF([QPointF(0, h1 - triangle_side_length_half),
                              QPointF(triangle_height, h1),
                              QPointF(0, h1 + triangle_side_length_half)])
        painter.drawPolygon(triangle)
        painter.drawLine(QPointF(triangle_height + triangle_side_length_half, h1),
                         QPointF(width, h1))

        # Draw second line
        painter.drawLine(QPointF(0, h2), QPointF(width, h2))

        # Draw third line, show FM text if needed
        if self._app.playlist.mode is PlaylistMode.fm:
            painter.drawLine(QPointF(0, h3), QPointF(width // 2, h3))
            painter.pen()
            pen.setColor(QColor(SOLARIZED_COLORS['blue']))
            painter.setPen(pen)
            font = painter.font()
            rect_h_half = line_margin // 2
            font.setPixelSize(int(rect_h_half * 2))
            painter.setFont(font)
            rect = QRectF(width // 2 + rect_h_half, h3 - rect_h_half,
                          width // 2 - rect_h_half, rect_h_half * 2)
            painter.drawText(rect, "FM", QTextOption(Qt.AlignCenter))
        else:
            painter.drawLine(QPointF(0, h3), QPointF(width, h3))

        painter.restore()
