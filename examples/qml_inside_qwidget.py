import os
import time

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtQuick import QQuickView

from feeluown.gui.widgets.comment_list import CommentListModel
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
reader = wrap([comment, comment2] * 1000)
QML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'demo.qml')


if __name__ == '__main__':
    app = QApplication([])
    widget = QWidget()
    view = QQuickView()
    model = CommentListModel(reader)
    view.setInitialProperties({"model": model})
    view.setSource(QUrl.fromLocalFile(QML_PATH))
    container = widget.createWindowContainer(view)
    layout = QVBoxLayout(widget)
    layout.addWidget(container)
    widget.show()
    widget.resize(600, 400)
    app.exec()
