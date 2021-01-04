from datetime import datetime

from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QSize, \
    QPoint, QRect
from PyQt5.QtGui import QPalette, QPen, QFont
from PyQt5.QtWidgets import QStyledItemDelegate, QListView, QSizePolicy, QFrame

from feeluown.gui.helpers import ItemViewNoScrollMixin


def human_readable_number_v1(n):
    levels = [(100000000, '亿'),
              (10000, '万')]
    for value, unit in levels:
        if n > value:
            first, second = n // value, (n % value) // (value // 10)
            return f'{first}.{second}{unit}'
    else:
        return str(n)


class CommentListModel(QAbstractListModel):
    def __init__(self, reader, parent=None):
        super().__init__(parent)

        self._reader = reader

    def rowCount(self, _=QModelIndex()):
        return self._reader.count

    def columnCount(self, _=QModelIndex()):
        return 1

    def flags(self, index):
        if not index.isValid():
            return 0
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return flags

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.UserRole:
            return self._reader.read(index.row())
        return None


class CommentListDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent=parent)

        self._margin_h = 10
        self._margin_v = 10
        self._name_content_margin = 5
        self._name_height = 15

    def paint(self, painter, option, index):
        painter.save()
        comment = index.data(Qt.UserRole)

        # size for render comment
        width = option.rect.width() - self._margin_h * 2
        height = option.rect.height() - self._margin_v * 2

        painter.translate(QPoint(option.rect.x() + self._margin_h,
                                 option.rect.y() + self._margin_v))

        # draw comment author name
        painter.save()
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        name_rect = QRect(0, 0, width, self._name_height)
        painter.drawText(name_rect, Qt.AlignLeft, comment.user.name)
        painter.restore()

        # draw comment other metadata
        painter.save()
        metadata_rect = QRect(0, 0, width, self._name_height)
        text_list = []
        if comment.time:
            dt = datetime.fromtimestamp(comment.time)
            text_list.append(dt.strftime('%Y-%m-%d %H:%M'))
        if comment.liked_count != -1:
            liked_count_text = human_readable_number_v1(comment.liked_count)
            text_list.append(f'♥ {liked_count_text}')
        text = '  |  '.join(text_list)
        text_color = option.palette.color(QPalette.Text)
        text_color.setAlpha(100)
        pen = QPen()
        pen.setColor(text_color)
        painter.setPen(pen)
        if text:
            painter.drawText(metadata_rect, Qt.AlignRight, text)
        painter.restore()

        # draw comment content
        painter.save()
        name_height = self._name_height + self._name_content_margin
        painter.translate(QPoint(0, name_height))
        content_height = height - name_height
        content_rect = QRect(0, 0, width, content_height)
        painter.drawText(content_rect,
                         Qt.TextWordWrap,
                         comment.content)
        painter.restore()

        # draw a dotted line under each row
        painter.save()
        painter.translate(QPoint(0, height + self._margin_v))
        text_color = option.palette.color(QPalette.Text)
        if text_color.lightness() > 150:
            non_text_color = text_color.darker(140)
        else:
            non_text_color = text_color.lighter(150)
        non_text_color.setAlpha(30)
        painter.setPen(QPen(non_text_color, 1, Qt.DotLine))
        painter.drawLine(QPoint(0, 0),  QPoint(width, 0))
        painter.restore()

        painter.restore()

    def sizeHint(self, option, index):
        parent_width = self.parent().width()
        fm = option.fontMetrics
        comment = index.data(Qt.UserRole)
        content_rect = fm.boundingRect(
            0, 0, parent_width, 0,
            Qt.AlignVCenter | Qt.TextWordWrap,
            comment.content
        )
        height = content_rect.height() + self._name_height + \
            self._name_content_margin + self._margin_v * 2
        return QSize(parent_width, height)


class CommentListView(ItemViewNoScrollMixin, QListView):

    def __init__(self, parent=None):
        super().__init__(parent)
        QListView.__init__(self, parent)

        self._delegate = CommentListDelegate(self)
        self.setItemDelegate(self._delegate)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setMouseTracking(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setResizeMode(QListView.Adjust)


if __name__ == '__main__':
    import time
    from PyQt5.QtWidgets import QApplication
    from feeluown.utils.reader import wrap
    from feeluown.library.models import CommentModel, BriefUserModel

    user = BriefUserModel(identifier='fuo-bot',
                          source='fuo',
                          name='随风而去')
    content = ('有没有一首歌会让你很想念，有没有一首歌你会假装听不见，'
               '听了又掉眼泪，却按不下停止健')
    comment = CommentModel(identifier='fuo',
                           source='fuo',
                           user=user,
                           like_count=1,
                           content=content,
                           time=int(time.time()),
                           parent=None,)
    comment2 = comment.copy()
    comment2.content = 'hello world'

    app = QApplication([])
    reader = wrap([comment, comment2, comment])
    model = CommentListModel(reader)
    widget = CommentListView()
    widget.setModel(model)
    widget.show()
    app.exec()
