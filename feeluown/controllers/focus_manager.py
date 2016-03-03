# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QApplication

from feeluown.view_api import ViewOp
from feeluown.widgets.playlist_widget import _BaseItem


class FocusManager(object):

    @classmethod
    def change_focus(cls):

        # TODO: other widget can add themselves to focusable_widgets
        focusable_widgets = [
            ViewOp.ui.WEBVIEW.tracks_table_widget,
            _BaseItem.items[2]]

        current_focus_widget = QApplication.focusWidget()
        if current_focus_widget in focusable_widgets:
            index = focusable_widgets.index(current_focus_widget)
            next_index = index + 1 if index < (len(focusable_widgets) - 1)\
                else 0
            focusable_widgets[next_index].setFocus()
        else:
            focusable_widgets[0].setFocus()
