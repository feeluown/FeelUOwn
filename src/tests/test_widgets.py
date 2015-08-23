# -*- coding:utf8 -*-


def test_desktop_mini_widget(qtbot):
    from widgets.desktop_mini import DesktopContainer
    w = DesktopContainer()
    w.show()
    qtbot.addWidget(w)


def test_setting_widget(qtbot):
    from widgets.setting_widget import SettingWidgetLayer
    w = SettingWidgetLayer()
    w.show()
    qtbot.addWidget(w)
