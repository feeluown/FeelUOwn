from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QPainter

from feeluown.gui.widgets import SelfPaintAbstractSquareButton
from feeluown.gui.widgets.selfpaint_btn import paint_round_bg_when_hover


class Avatar(SelfPaintAbstractSquareButton):

    def contextMenuEvent(self, e) -> None:
        menu = QMenu()
        menu.addAction('功能导航')
        menu.exec_(e.globalPos())

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_round_bg_when_hover(self, painter)

        pen = painter.pen()
        pen.setWidthF(1.5)
        painter.setPen(pen)

        # Draw circle.
        diameter = self.width() // 3
        painter.drawEllipse(diameter, self._padding, diameter, diameter)

        # Draw body.
        x, y = self._padding, self.height() // 2
        width, height = self.width() // 2, self.height() // 2
        painter.drawArc(x, y, width, height, 0, 60*16)
        painter.drawArc(x, y, width, height, 120*16, 60*16)


if __name__ == '__main__':
    from feeluown.gui.debug import simple_layout

    length = 400

    with simple_layout() as layout:
        layout.addWidget(Avatar(length=length))
