# -*- coding:utf8 -*-


def test_view(qtbot):
    from PyQt5.QtWidgets import QWidget
    from feeluown.ui import UiMainWidget
    w = QWidget()
    ui = UiMainWidget()
    ui.setup_ui(w)
    w.show()
    qtbot.addWidget(w)
