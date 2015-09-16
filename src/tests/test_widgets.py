# -*- coding:utf8 -*-


def test_desktop_mini_widget(qtbot):
    from widgets.desktop_mini import DesktopMiniContainer
    w = DesktopMiniContainer()
    w.show()
    qtbot.addWidget(w)


def test_setting_widget(qtbot):
    from widgets.desktop_mini import DesktopMiniLayer
    w = DesktopMiniLayer()
    w.show()
    qtbot.addWidget(w)


def test_music_table_widget(qtbot):
    from widgets.music_table_widget import MusicTableWidget
    w = MusicTableWidget()
    w.show()
    qtbot.addWidget(w)


def test_notify_widget(qtbot):
    from widgets.notify import NotifyWidget
    w = NotifyWidget()
    w.show()
    qtbot.addWidget(w)
