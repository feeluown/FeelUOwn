import time
from feeluown.utils.reader import create_reader
from feeluown.library.models import CommentModel, BriefUserModel, BriefCommentModel
from feeluown.gui.widgets.comment_list import CommentListModel, CommentListView


def test_comment_list_view(qtbot):
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
    comment2 = comment.model_copy()
    comment2.content = 'hello world'

    reader = create_reader([comment, comment2, comment])
    model = CommentListModel(reader)
    widget = CommentListView()
    widget.setModel(model)
    widget.show()

    qtbot.addWidget(widget)
