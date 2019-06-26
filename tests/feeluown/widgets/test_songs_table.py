import time

import pytest

from tests.helpers import is_travis_env
from feeluown.widgets.songs_table_meta import SongsTableMetaWidget


# TODO: use xvfb in travis env
# example: https://github.com/pytest-dev/pytest-qt/blob/master/.travis.yml
@pytest.mark.skipif(is_travis_env, reason="travis env has no display")
def test_songs_table_meta(qtbot):
    widget = SongsTableMetaWidget()
    widget.title = '我喜欢的音乐'
    widget.subtitle = '嘿嘿'
    widget.creator = 'cosven'
    widget.updated_at = time.time()
    widget.desc = "<pre><code>print('hello world')</code><pre>"

    qtbot.addWidget(widget)
