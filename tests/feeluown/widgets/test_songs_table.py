import time

from feeluown.widgets.songs_table_meta import SongsTableMetaWidget


def test_songs_table_meta(qtbot):
    widget = SongsTableMetaWidget()
    widget.title = '我喜欢的音乐'
    widget.subtitle = '嘿嘿'
    widget.creator = 'cosven'
    widget.updated_at = time.time()
    widget.desc = "<pre><code>print('hello world')</code><pre>"

    qtbot.addWidget(widget)
