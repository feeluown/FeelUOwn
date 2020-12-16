"""
Table of contents view for one collection
"""

from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex, QSize,
                          QRect, QPoint, pyqtSignal)
from PyQt5.QtGui import (QPainter, QPalette, QPen)
from PyQt5.QtWidgets import (QListView, QStyledItemDelegate, QStyle,
                             QSizePolicy, QFrame, QVBoxLayout)

from feeluown.models import ModelType
from feeluown.gui.helpers import resize_font
from feeluown.widgets.meta import CollMetaWidget
from feeluown.widgets.songs import SongListView


def draw_album_icon(painter, x, y, h):
    r = h // 2
    center_x, center_y = x + r, y + r
    circle_center = QPoint(center_x, center_y)
    pen = painter.pen()
    pen.setCapStyle(Qt.RoundCap)
    pen.setWidth(2)
    painter.setPen(pen)
    r = r - 3  # margin
    r_dis = r // 4
    r_list = (r, r - 3 * r_dis, 2)
    for radius in r_list:
        painter.drawEllipse(circle_center, radius, radius)

    arc_list = [
        (r - r_dis, 16, 60),      # outer arc
        (r - r_dis * 2, 20, 50),  # inner arc
    ]
    for arc_r, start_angle, span in arc_list:
        topleft = QPoint(center_x - arc_r, center_y - arc_r)
        bottomright = QPoint(center_x + arc_r, center_y + arc_r)
        painter.drawArc(QRect(topleft, bottomright), 16 * start_angle, 16 * span)
        painter.drawArc(QRect(topleft, bottomright), 16 * (start_angle + 180), 16 * span)


class CollectionBody(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.meta_widget = CollMetaWidget(self)
        self.song_list_view = SongListView(self)

        self._layout = QVBoxLayout(self)
        self._setup_ui()

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(300, size.height())

    def _setup_ui(self):

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.meta_widget)
        self._layout.addWidget(self.song_list_view)


class CollectionTOCModel(QAbstractListModel):
    def __init__(self, coll, parent=None):
        super().__init__(parent)

        self.coll = coll
        self.albums = []
        self.artists = []
        self.songs = []

        for model in self.coll.models:
            if model.meta.model_type == ModelType.album:
                self.albums.append(model)
            elif model.meta.model_type == ModelType.artist:
                self.artits.append(model)
            elif model.meta.model_type == ModelType.song:
                self.songs.append(model)

        self.items = self.albums + self.songs

    def rowCount(self, _=QModelIndex()):
        return len(self.items)

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        model = self.items[row]
        if role == Qt.UserRole:
            return model
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

        model = index.data(Qt.UserRole)
        rect = option.rect

        # calculate geometry for model icon
        icon_margin_left = 3
        topleft = rect.topLeft()
        icon_x, icon_y = topleft.x() + icon_margin_left, topleft.y() + 1
        icon_w = icon_h = rect.height() - 2
        text_x = icon_x + icon_w + 5
        text_y = topleft.y()
        text_topleft = QPoint(text_x, text_y)

        text_color = option.palette.color(QPalette.Text)
        if text_color.lightness() > 150:
            bonus_text_color = text_color.darker(140)
        else:
            bonus_text_color = text_color.lighter(140)

        if model.meta.model_type == ModelType.album:
            draw_album_icon(painter, icon_x, icon_y, icon_h)
            text = model.name_display
            text_rect = QRect(text_topleft, rect.bottomRight())
            painter.drawText(text_rect, Qt.AlignVCenter, text)
        elif model.meta.model_type == ModelType.song:
            text = model.title_display
            mid_y = rect.y() + rect.height() // 2
            title_bottomright = QPoint(rect.right(), mid_y)
            title_rect = QRect(text_topleft, title_bottomright)
            painter.drawText(title_rect, Qt.AlignVCenter, text)

            # draw bonus text
            font = painter.font()
            resize_font(font, - 2)
            painter.setFont(font)
            pen = painter.pen()
            pen.setColor(bonus_text_color)
            painter.setPen(pen)
            bonus_rect = QRect(QPoint(text_x, mid_y), rect.bottomRight())
            bonus_text = model.artists_name_display + ' - ' + model.album_name_display
            painter.drawText(bonus_rect, Qt.AlignVCenter, bonus_text)

            # draw model icon
            # TODO: draw icon by using shapes, instead of text
            pen.setColor(text_color)
            painter.setPen(pen)
            font = painter.font()
            font.setPointSize(30)
            painter.setFont(font)
            painter.drawText(
                QRect(QPoint(icon_x, icon_y),
                      QPoint(icon_x + icon_h, icon_y + icon_h)),
                Qt.AlignCenter,
                '♬'
            )

        painter.restore()

    def sizeHint(self, option, index):
        if index.isValid():
            return QSize(100, 45)
        return super().sizeHint(option, index)


class CollectionTOCView(QListView):

    show_album_needed = pyqtSignal([object])
    play_song_needed = pyqtSignal([object])

    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        delegate = CollectionTOCDelegate(self)
        self.setItemDelegate(delegate)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)
        self.setFrameShape(QFrame.NoFrame)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        model = index.data(Qt.UserRole)
        if model.meta.model_type == ModelType.album:
            self.show_album_needed.emit(model)
        elif model.meta.model_type == ModelType.song:
            self.play_song_needed.emit(model)

    def sizeHint(self):
        size = super().sizeHint()
        return QSize(150, size.height())


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    view = CollectionTOCView(None)
    model = CollectionTOCModel(view)
    view.setModel(model)
    view.show()
    app.exec()
