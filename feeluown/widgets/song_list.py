from PyQt5.QtCore import (QAbstractListModel, QModelIndex, Qt, QRect,
                          QPoint, QSize, pyqtSignal, QEvent)
from PyQt5.QtGui import (QPainter, QPalette, QPen, QMouseEvent)
from PyQt5.QtWidgets import (QListView, QStyledItemDelegate, QStyle, QSizePolicy,
                             QApplication, QStyleOptionButton, QFrame)


class SongListModel(QAbstractListModel):
    def __init__(self, reader, parent=None):
        super().__init__(parent)

        self._songs = []  # songs read from reader
        self._can_fetch_more = True
        self._reader = reader

    def rowCount(self, _=QModelIndex()):
        return len(self._songs)

    def fetchMore(self, _=QModelIndex()):
        fetched, total = 0, 30
        songs = []
        for song in self._reader:
            fetched += 1
            songs.append(song)
            if fetched >= total:
                break
        else:
            self._can_fetch_more = False
        begin = len(self._songs)
        self.beginInsertRows(QModelIndex(), begin, begin + len(songs) - 1)
        self._songs.extend(songs)
        self.endInsertRows()

    def canFetchMore(self, _):
        return self._can_fetch_more

    def flags(self, index):
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return flags

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == Qt.DisplayRole:
            return self._songs[row].title_display
        elif role == Qt.UserRole:
            return self._songs[row]
        return None


class SongListDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent=parent)

        # the rect.x the number text
        self.number_rect_x = 40
        self.play_btn_pressed = False

    def paint(self, painter, option, index):
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        text_color = option.palette.color(QPalette.Text)
        if text_color.lightness() > 150:
            non_text_color = text_color.darker(140)
        else:
            non_text_color = text_color.lighter(140)
        text_pen = QPen(text_color)
        non_text_pen = QPen(non_text_color)
        hl_text_pen = QPen(option.palette.color(QPalette.HighlightedText))
        if option.state & QStyle.State_Selected:
            painter.setPen(hl_text_pen)
        else:
            painter.setPen(text_pen)

        song = index.data(Qt.UserRole)
        top = option.rect.top()
        bottom = option.rect.bottom()
        no_x = self.number_rect_x
        duration_x = option.rect.topRight().x() - 50
        no_bottom_right = QPoint(no_x, bottom)
        text_top_left = QPoint(no_x + 10, top)
        text_bottom_right = QPoint(duration_x, bottom)
        duration_top_left = QPoint(duration_x, top)
        no_rect = QRect(option.rect.topLeft(), no_bottom_right)
        text_rect = QRect(text_top_left, text_bottom_right)
        duration_rect = QRect(duration_top_left, option.rect.bottomRight())
        painter.drawText(text_rect, Qt.AlignVCenter, song.title_display)

        painter.setPen(non_text_pen)
        if option.state & QStyle.State_MouseOver:
            opt = QStyleOptionButton()
            opt.text = '►'
            opt.palette = option.palette
            opt.state = QStyle.State_Enabled
            opt.rect = no_rect
            QApplication.style().drawControl(QStyle.CE_PushButton, opt, painter)
        else:
            painter.drawText(no_rect, Qt.AlignCenter, str(index.row() + 1))
        painter.drawText(duration_rect, Qt.AlignCenter, song.duration_ms_display)
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
            no_bottom_right = QPoint(self.number_rect_x, option.rect.bottom())
            no_rect = QRect(option.rect.topLeft(), no_bottom_right)
            mouse_event = QMouseEvent(event)
            if no_rect.contains(mouse_event.pos()):
                if event.type() == QEvent.MouseButtonPress:
                    self.play_btn_pressed = True
                if event.type() == QEvent.MouseButtonRelease:
                    if self.play_btn_pressed is True:
                        self.parent().play_song_needed.emit(index.data(Qt.UserRole))
            if event.type() == QEvent.MouseButtonRelease:
                self.play_btn_pressed = False
        return super().editorEvent(event, model, option, index)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if index.isValid():
            return QSize(size.width(), 36)
        return size


class SongListView(QListView):

    play_song_needed = pyqtSignal([object])

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.delegate = SongListDelegate(self)
        self.setItemDelegate(self.delegate)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setMouseTracking(True)
        self.setFrameShape(QFrame.NoFrame)
        self.activated.connect(self._on_activated)

    def _on_activated(self, index):
        self.play_song_needed.emit(index.data(Qt.UserRole))


if __name__ == '__main__':
    from fuocore.reader import RandomSequentialReader

    class Song:
        title_display = 'hello world'

    songs = [Song() for i in range(0, 10)]
    reader = RandomSequentialReader.from_list(songs)

    app = QApplication([])
    view = SongListView(None)
    model = SongListModel(reader)
    view.setModel(model)
    view.show()
    app.exec()
