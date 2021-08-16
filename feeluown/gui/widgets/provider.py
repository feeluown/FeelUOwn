import math

from PyQt5.QtCore import Qt, QSize, QRectF, QRect, QPoint
from PyQt5.QtGui import QPainter, QTextOption, QPalette, QBrush, QColor, \
    QGuiApplication  # noqa
from PyQt5.QtWidgets import QStyledItemDelegate, QListView
from PyQt5.QtSvg import QSvgRenderer

from feeluown.library import ModelType, ProviderFlags as PF
from feeluown.gui.helpers import ItemViewNoScrollMixin, resize_font, SOLARIZED_COLORS
from .textlist import TextlistModel


class ProvidersModel(TextlistModel):
    def __init__(self, library, parent=None):
        super().__init__(parent)
        self._library = library
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
        provider_ui_item = self._association[provider_id]
        if role == Qt.DisplayRole:
            return provider_ui_item.symbol + ' ' + provider_ui_item.text
        if role == Qt.ToolTipRole:
            if self._library.check_flags(
                    provider_id, ModelType.none, PF.current_user):
                provider = provider_ui_item.provider
                if provider.has_current_user():
                    return '已登录'
                return f'{provider_ui_item.desc}'
            return f'[{provider_ui_item.text}] {provider_ui_item.desc}'
        if role == Qt.UserRole:
            return provider_ui_item
        return super().data(index, role)


class ProvidersDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, library=None):
        super().__init__(parent)
        self._library = library

        self._radius = 22
        self._padding = 6

        self.__body_radius = self._radius - self._padding
        self.__text_rect_x = self.__body_radius - self.__body_radius / math.sqrt(2)
        self.__text_rect_width = 2 * (self.__body_radius / math.sqrt(2))

    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.Antialiasing)
        provider_ui_item = index.data(Qt.UserRole)

        painter.save()
        painter.translate(self._padding + option.rect.x(),
                          self._padding + option.rect.y())

        w = h = (self._radius - self._padding) * 2
        body_rect = QRect(0, 0, w, h)

        if provider_ui_item.colorful_svg:
            svg_renderer = QSvgRenderer(provider_ui_item.colorful_svg)
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
            painter.drawText(QRectF(text_rect), provider_ui_item.text, text_option)
            painter.restore()

        # TODO: use library.check_flags instead of provider.check_flags
        provider = provider_ui_item.provider
        if self._library.check_flags(
                provider.identifier, ModelType.none, PF.current_user):
            if provider.has_current_user():
                painter.save()
                bottom_right = body_rect.bottomRight()
                status_radius = self._radius // 5
                x = bottom_right.x() - status_radius * 2
                y = bottom_right.y() - status_radius * 2
                status_rect = QRect(QPoint(x, y), bottom_right)
                pen = painter.pen()
                pen.setWidth(2)
                pen.setColor(QGuiApplication.palette().color(QPalette.Window))
                painter.setPen(pen)
                painter.setBrush(QColor(SOLARIZED_COLORS['blue']))
                painter.drawRoundedRect(status_rect, status_radius, status_radius)
                painter.restore()

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(self._radius * 2, self._radius * 2)


class ProvidersView(ItemViewNoScrollMixin, QListView):
    def __init__(self, parent, library):
        super().__init__(parent)
        QListView.__init__(self, parent=parent)
        self._library = library

        self._reserved = 10
        self._least_row_count = 1
        self._row_height = 48

        self.delegate = ProvidersDelegate(self, library=library)
        self.setItemDelegate(self.delegate)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        provider_ui_item = index.data(role=Qt.UserRole)
        provider_ui_item.clicked.emit()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.adjust_height()
