from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QSize, QRectF
from PyQt5.QtGui import QPainter, QTextOption, QPalette, QBrush  # noqa
from PyQt5.QtWidgets import QStyledItemDelegate, QListView

from feeluown.gui.helpers import ItemViewNoScrollMixin, resize_font, ReaderFetchMoreMixin
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
            return provider.desc
        if role == Qt.UserRole:
            return provider
        return super().data(index, role)


class ProvidersDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.Antialiasing)
        provider = index.data(Qt.UserRole)
        ch = provider._name[0].capitalize()

        painter.save()
        text_color = option.palette.color(QPalette.Text)
        if text_color.lightness() > 150:
            non_text_color = text_color.darker(140)
        else:
            non_text_color = text_color.lighter(150)
        non_text_color.setAlpha(100)
        brush = QBrush(non_text_color)
        painter.setBrush(brush)
        painter.drawRoundedRect(option.rect, 24, 24)
        painter.restore()

        painter.save()
        font = painter.font()
        resize_font(font, +4)
        text_option = QTextOption()
        text_option.setAlignment(Qt.AlignCenter)
        painter.drawText(QRectF(option.rect), ch, text_option)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(48, 48)


class ProvidersView(QListView):
    def __init__(self, parent):
        super().__init__()
        QListView.__init__(self, parent=parent)

        self.delegate = ProvidersDelegate(self)
        self.setItemDelegate(self.delegate)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWrapping(True)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        provider = index.data(role=Qt.UserRole)
        provider.clicked.emit()
