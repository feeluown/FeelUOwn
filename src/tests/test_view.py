# -*- coding:utf8 -*-


def test_view(qtbot):
    from views import UiMainWidget
    from PyQt5.QtWidgets import QWidget
    w = QWidget()
    ui = UiMainWidget()
    ui.setup_ui(w)
    w.show()
    qtbot.addWidget(w)