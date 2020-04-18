"""
Table of contents view for one collection
"""

from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex, QSize,
                          QRectF, QRect, QPoint, )
from PyQt5.QtGui import (QPainter, QPalette, QPen, QTextOption)
from PyQt5.QtWidgets import QListView, QStyledItemDelegate, QStyle


class CollectionTOCModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.items = list(['理性与感性', '单身日志（Live）', '叶慧美', '晴日共剪窗'])

    def rowCount(self, _=QModelIndex()):
        return len(self.items)

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == Qt.DisplayRole:
            return self.items[row]
        return None


class CollectionTOCDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def paint(self, painter, option, index):
        # refer to pixelator.py
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        text_pen = QPen(option.palette.color(QPalette.Text))
        hl_text_pen = QPen(option.palette.color(QPalette.HighlightedText))
        if option.state & QStyle.State_Selected:
            painter.setPen(hl_text_pen)
        else:
            painter.setPen(text_pen)

        # draw circle
        topleft = option.rect.topLeft()
        x, y = topleft.x(), topleft.y()
        r = option.rect.height() // 2
        center_x = x + r
        center_y = y + r
        circle_center = QPoint(center_x, center_y)
        # painter.drawEllipse(circle_center, r, r)

        flags = Qt.AlignCenter
        circle_rect = QRect(x, y, 2*r, 2*r)
        font = painter.font()
        font.setPointSize(r//2)
        painter.setFont(font)

        # draw icon
        # if index.row() % 2 != 0:
        #     painter.drawText(circle_rect, flags, '♪')
        # else:
        #     painter.drawText(circle_rect, flags, '♪')

        pen = painter.pen()
        pen.setCapStyle(Qt.RoundCap)
        pen.setWidth(2)
        painter.setPen(pen)
        r = 22
        r_dis = 5
        painter.drawEllipse(circle_center, r, r)
        painter.drawEllipse(circle_center, r - 3 * r_dis, r - 3 * r_dis)
        painter.drawEllipse(circle_center, r - 4 * r_dis, r - 4 * r_dis)

        # outer arc
        arc_r = r - r_dis
        topleft = QPoint(center_x - arc_r, center_y - arc_r)
        bottomright = QPoint(center_x + arc_r, center_y + arc_r)
        start_angle = 16
        span = 60
        painter.drawArc(QRect(topleft, bottomright), 16 * start_angle, 16 * span)
        painter.drawArc(QRect(topleft, bottomright), 16 * (start_angle + 180), 16 * span)

        # inner arc
        inner_arc_r = arc_r - r_dis
        start_angle = 20
        span = 50
        topleft = QPoint(center_x - inner_arc_r, center_y - inner_arc_r)
        bottomright = QPoint(center_x + inner_arc_r, center_y + inner_arc_r)
        painter.drawArc(QRect(topleft, bottomright), 16 * start_angle, 16 * span)
        painter.drawArc(QRect(topleft, bottomright), 16 * (start_angle + 180), 16 * span)

        text = index.data(Qt.DisplayRole)
        topleft = option.rect.topLeft()
        topleft = QPoint(topleft.x() + 2*r + 15, topleft.y())
        painter.drawText(QRect(topleft, option.rect.bottomRight()), Qt.AlignVCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        if index.isValid():
            return QSize(100, 50)
        return super().sizeHint(option, index)


class CollectionTOCView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        delegate = CollectionTOCDelegate(self)
        self.setItemDelegate(delegate)



if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    view = CollectionTOCView()
    model = CollectionTOCModel(view)
    view.setModel(model)
    view.show()
    app.exec()
