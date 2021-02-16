from PyQt5.QtCore import Qt, QRectF, QPoint
from PyQt5.QtGui import QTextOption
from PyQt5.QtWidgets import QToolTip

from feeluown.gui.widgets.statusline import StatuslineLabel


class NotifyStatus(StatuslineLabel):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        self._app = app

    def drawInner(self, painter):
        inner_rect = QRectF(0, 0, self._inner_width, self._inner_height)
        painter.drawText(inner_rect, '✉', QTextOption(Qt.AlignCenter))

    def show_msg(self, text, timeout=1500):
        QToolTip.showText(self.mapToGlobal(QPoint(0, 0)),
                          text,
                          self,
                          self.rect(),
                          timeout)
