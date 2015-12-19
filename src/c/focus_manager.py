# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QApplication

from view_api import ViewOp
from widgets.playlist_widget import _BaseItem


class FocusManager(object):
    @classmethod
    def change_focus(cls):
        if QApplication.focusWidget() is ViewOp.ui.WEBVIEW:
            _BaseItem.items[1].setFocus()
        else:
            ViewOp.ui.WEBVIEW.setFocus()
