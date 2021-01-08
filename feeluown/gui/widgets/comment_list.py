from datetime import datetime

from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, QSize, \
    QPoint, QRect
from PyQt5.QtGui import QPalette, QPen, QFont
from PyQt5.QtWidgets import QStyledItemDelegate, QListView, QSizePolicy, QFrame

from feeluown.gui.helpers import ItemViewNoScrollMixin, Paddings, Margins


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
        self._parent_comment_paddings = Paddings(8, 3, 8, 3)
        self._parent_comment_margins = Margins(20, 5, 10, 5)

    def paint(self, painter, option, index):
        painter.save()
        comment = index.data(Qt.UserRole)
        fm = option.fontMetrics

        # size for render comment
        body_width = option.rect.width() - self._margin_h * 2
        body_height = option.rect.height() - self._margin_v * 2

        painter.translate(QPoint(option.rect.x() + self._margin_h,
                                 option.rect.y() + self._margin_v))

        # draw comment author name
        painter.save()
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        name_rect = QRect(0, 0, body_width, self._name_height)
        painter.drawText(name_rect, Qt.AlignLeft, comment.user.name)
        painter.restore()

        # draw comment other metadata
        painter.save()
        metadata_rect = QRect(0, 0, body_width, self._name_height)
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
        content_height = self._get_text_height(fm, body_width, comment.content)
        content_rect = QRect(0, 0, body_width, content_height)
        painter.drawText(content_rect,
                         Qt.TextWordWrap,
                         comment.content)
        parent_comment = comment.parent
        if parent_comment is not None:
            p_margins = self._parent_comment_margins
            p_paddings = self._parent_comment_paddings
            text = f'{parent_comment.user_name}：{parent_comment.content}'
            p_width = body_width - p_margins.width
            p_height = self._get_text_height(fm, p_width, text)
            p_body_rect = QRect(p_margins.left, p_margins.top + content_height,
                                p_width, p_height + p_paddings.height)
            p_content_rect = QRect(p_body_rect.x() + p_paddings.left,
                                   p_body_rect.y() + p_paddings.top,
                                   p_body_rect.width() - p_paddings.width,
                                   p_body_rect.height() - p_paddings.height)
            bg_color = option.palette.color(QPalette.Window)
            if bg_color.lightness() > 150:
                bg_color = bg_color.darker(100)
            else:
                bg_color = bg_color.lighter(100)
            painter.fillRect(p_body_rect, bg_color)
            painter.drawText(p_content_rect, Qt.TextWordWrap, text)

        painter.restore()

        # draw a dotted line under each row
        painter.save()
        painter.translate(QPoint(0, body_height + self._margin_v))
        text_color = option.palette.color(QPalette.Text)
        if text_color.lightness() > 150:
            non_text_color = text_color.darker(140)
        else:
            non_text_color = text_color.lighter(150)
        non_text_color.setAlpha(30)
        painter.setPen(QPen(non_text_color, 1, Qt.DotLine))
        painter.drawLine(QPoint(0, 0),  QPoint(body_width, 0))
        painter.restore()

        painter.restore()

    def sizeHint(self, option, index):
        super_size_hint = super().sizeHint(option, index)
        parent_width = self.parent().width()
        fm = option.fontMetrics
        comment = index.data(Qt.UserRole)
        content_width = parent_width - 2 * self._margin_h
        content_height = self._get_text_height(fm, content_width, comment.content)
        height = content_height + self._name_height + \
            self._name_content_margin + self._margin_v * 2
        parent_comment = comment.parent
        if parent_comment is not None:
            p_margins = self._parent_comment_margins
            p_paddings = self._parent_comment_paddings
            text = f'{parent_comment.user_name}：{parent_comment.content}'
            p_height = self._get_text_height(fm, content_width - p_margins.width, text)
            height += p_height + p_margins.height + p_paddings.height
        return QSize(super_size_hint.width(), height)

    def _get_text_height(self, fm, width, text):
        return fm.boundingRect(
            0, 0, width, 0,
            Qt.AlignVCenter | Qt.TextWordWrap,
            text
        ).height()


class CommentListView(ItemViewNoScrollMixin, QListView):

    def __init__(self, parent=None):
        super().__init__(parent)
        QListView.__init__(self, parent)

        self._delegate = CommentListDelegate(self)
        self.setItemDelegate(self._delegate)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setMouseTracking(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setResizeMode(QListView.Adjust)

    def min_height(self):
        """
        override ItemViewNoScrollMixin.min_height
        """
        model = self.model()
        if model is None:
            return super().min_height()
        row_count = model.rowCount()
        height = self._reserved
        while row_count >= 0:
            row_count -= 1
            height += self.sizeHintForRow(row_count)
        return height


if __name__ == '__main__':
    import time
    from PyQt5.QtWidgets import QApplication
    from feeluown.utils.reader import wrap
    from feeluown.library.models import CommentModel, BriefUserModel, BriefCommentModel

    user = BriefUserModel(identifier='fuo-bot',
                          source='fuo',
                          name='随风而去')
    content = ('有没有一首歌会让你很想念，有没有一首歌你会假装听不见，'
               '听了又掉眼泪，却按不下停止健')
    brief_comment = BriefCommentModel(identifier='ouf',
                                      user_name='world',
                                      content='有没有人曾告诉你')
    comment = CommentModel(identifier='fuo',
                           source='fuo',
                           user=user,
                           liked_count=1,
                           content=content,
                           time=int(time.time()),
                           parent=brief_comment,)
    comment2 = comment.copy()
    comment2.content = 'hello world'

    app = QApplication([])
    reader = wrap([comment, comment2, comment])
    model = CommentListModel(reader)
    widget = CommentListView()
    widget.setModel(model)
    widget.show()
    app.exec()
