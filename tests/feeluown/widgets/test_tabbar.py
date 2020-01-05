import pytest

from tests.helpers import cannot_run_qt_test
from feeluown.widgets.tabbar import TableTabBar


# TODO: use xvfb in travis env
# example: https://github.com/pytest-dev/pytest-qt/blob/master/.travis.yml
@pytest.mark.skipif(cannot_run_qt_test, reason='this is a qt testcase')
def test_tabbar(qtbot):
    tabbar = TableTabBar()
    qtbot.addWidget(tabbar)
    tabbar.artist_mode()
    with qtbot.waitSignal(tabbar.show_albums_needed):
        tabbar.tabBarClicked.emit(1)

    tabbar.library_mode()
    with qtbot.waitSignal(tabbar.show_artists_needed):
        tabbar.tabBarClicked.emit(1)
