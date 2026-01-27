from datetime import datetime

import pytest
from PyQt6.QtWidgets import QWidget

from tests.helpers import is_travis_env
from feeluown.gui.widgets.meta import TableMetaWidget


# TODO: use xvfb in travis env
# example: https://github.com/pytest-dev/pytest-qt/blob/master/.travis.yml
@pytest.mark.skipif(is_travis_env, reason="travis env has no display")
def test_table_meta(qtbot, app_mock):
    p_widget = QWidget()
    widget = TableMetaWidget(app_mock, p_widget)
    qtbot.addWidget(p_widget)
    widget.title = '我喜欢的音乐'
    widget.subtitle = '嘿嘿'
    widget.creator = 'cosven'
    widget.updated_at = datetime.now()
    widget.desc = "<pre><code>print('hello world')</code><pre>"
