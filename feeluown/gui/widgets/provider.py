import math

from PyQt5.QtCore import Qt, QSize, QRectF, QRect, QUrl
from PyQt5.QtGui import QPainter, QTextOption, QPalette, QBrush  # noqa
from PyQt5.QtWidgets import QStyledItemDelegate, QListView
from PyQt5.QtSvg import QSvgRenderer

from feeluown.gui.helpers import ItemViewNoScrollMixin, resize_font
from .textlist import TextlistModel


class ProvidersModel(TextlistModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._association = {}

    def assoc(self, provider_id, pm):
        self._association[provider_id] = pm
        self.add(provider_id)

    def remove(self, provider_id):
        if not self._association.pop(provider_id, None):
            self.remove(provider_id)

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        provider_id = self._items[row]
        provider = self._association[provider_id]
        if role == Qt.DisplayRole:
            return provider.symbol + ' ' + provider.text
        if role == Qt.ToolTipRole:
            return f'[{provider.text}] {provider.desc}'
        if role == Qt.UserRole:
            return provider
        return super().data(index, role)


class ProvidersDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._radius = 20
        self._padding = 3

        self.__body_radius = self._radius - self._padding
        self.__text_rect_x = self.__body_radius - self.__body_radius / math.sqrt(2)
        self.__text_rect_width = 2 * (self.__body_radius / math.sqrt(2))

    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.Antialiasing)
        provider = index.data(Qt.UserRole)

        painter.save()
        painter.translate(self._padding + option.rect.x(),
                          self._padding + option.rect.y())

        w = h = (self._radius - self._padding) * 2
        body_rect = QRect(0, 0, w, h)

        if provider.colorful_svg:
            svg_renderer = QSvgRenderer(QUrl(provider.colorful_svg).toString())
            svg_renderer.render(painter, QRectF(body_rect))
        else:
            # draw rounded rect
            painter.save()
            text_color = option.palette.color(QPalette.Text)
            if text_color.lightness() > 150:
                non_text_color = text_color.darker(140)
            else:
                non_text_color = text_color.lighter(150)
            non_text_color.setAlpha(100)
            pen = painter.pen()
            pen.setColor(non_text_color)
            painter.setPen(pen)
            painter.drawRoundedRect(body_rect, w//2, h//2)
            painter.restore()

            painter.save()
            font = painter.font()
            resize_font(font, -3)
            painter.setFont(font)
            text_option = QTextOption()
            text_option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            text_option.setAlignment(Qt.AlignCenter)

            text_rect = QRectF(self.__text_rect_x, self.__text_rect_x,
                               self.__text_rect_width, self.__text_rect_width)
            painter.drawText(QRectF(text_rect), provider.text, text_option)
            painter.restore()
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(self._radius * 2, self._radius * 2)


class ProvidersView(ItemViewNoScrollMixin, QListView):
    def __init__(self, parent):
        super().__init__(parent)
        QListView.__init__(self, parent=parent)

        self._reserved = 10
        self._least_row_count = 1
        self._row_height = 48

        self.delegate = ProvidersDelegate(self)
        self.setItemDelegate(self.delegate)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        provider = index.data(role=Qt.UserRole)
        provider.clicked.emit()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.adjust_height()
