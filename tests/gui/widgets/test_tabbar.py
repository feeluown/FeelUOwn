import pytest

from tests.helpers import cannot_run_qt_test
from feeluown.gui.widgets.tabbar import TableTabBar


@pytest.mark.skipif(cannot_run_qt_test, reason='')
def test_tabbar(qtbot):
    tabbar = TableTabBar()
    qtbot.addWidget(tabbar)
    tabbar.artist_mode()
    with qtbot.waitSignal(tabbar.show_albums_needed):
        tabbar.tabBarClicked.emit(1)

    tabbar.library_mode()
    with qtbot.waitSignal(tabbar.show_artists_needed):
        tabbar.tabBarClicked.emit(1)
