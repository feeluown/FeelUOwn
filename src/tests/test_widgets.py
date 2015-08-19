# -*- coding:utf8 -*-


def test_falldown_widget(qtbot):
    from widgets.desktop_mini import DesktopContainer
    w = DesktopContainer()
    w.show()
    qtbot.addWidget(w)