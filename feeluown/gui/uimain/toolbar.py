from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QStackedWidget

from feeluown.gui.widgets import (
    LeftArrowButton,
    RightArrowButton,
    SearchSwitchButton,
    SettingsButton,
)
from feeluown.gui.widgets.magicbox import MagicBox
from feeluown.gui.widgets.statusline import StatusLine

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

ButtonSize = (30, 30)
ButtonSpacing = int(ButtonSize[0] / 6)


class ToolbarButton(QPushButton):

    def __init__(self, text, parent=None):
        super().__init__(text, parent=parent)


class BottomPanel(QWidget):

    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.back_btn = LeftArrowButton(length=ButtonSize[0])
        self.forward_btn = RightArrowButton(length=ButtonSize[0])

        self.magicbox = MagicBox(self._app)

        self._stack_switch = SearchSwitchButton(length=ButtonSize[0])
        self._stack_switch.setToolTip("显示搜索框")
        self._stack_switch.setCheckable(True)
        self._stacked_widget = QStackedWidget(self)
        self._stacked_widget.addWidget(self.magicbox)
        self._stack_switch.hide()

        self.status_line = StatusLine(self._app)
        self.settings_btn = SettingsButton(length=ButtonSize[0])

        # initialize widgets
        self.back_btn.setEnabled(False)
        self.forward_btn.setEnabled(False)

        self.back_btn.clicked.connect(self._app.browser.back)
        self.forward_btn.clicked.connect(self._app.browser.forward)
        self._stack_switch.clicked.connect(self._show_next_stacked_widget)
        self._stack_switch.toggled.connect(self._on_stack_switch_toggled)
        self._stacked_widget.currentChanged.connect(self._on_stacked_widget_changed)

        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName('bottom_panel')

        self._layout.addWidget(self.back_btn)
        self._layout.addWidget(self.forward_btn)

        self._layout.addSpacing(80)
        self._layout.addWidget(self._stacked_widget)
        self._layout.addWidget(self._stack_switch)
        self._layout.addSpacing(40)
        self._layout.addWidget(self.status_line)
        self._layout.addWidget(self.settings_btn)

        # assume the magicbox height is about 30
        # h_margin = 20(TableContainer h_spacing) - 30*0.25(back_btn padding)
        h_margin, v_margin = 11, 7
        height = self.magicbox.height()

        self.setFixedHeight(height + v_margin * 2 + 8)
        self._layout.setContentsMargins(h_margin, v_margin, h_margin, v_margin)
        self._layout.setAlignment(self._stacked_widget, Qt.AlignVCenter)
        self._layout.setSpacing(ButtonSpacing)

    def _show_next_stacked_widget(self):
        current_index = self._stacked_widget.currentIndex()
        if current_index < self._stacked_widget.count() - 1:
            next_index = current_index + 1
        else:
            next_index = 0
        self._stacked_widget.setCurrentIndex(next_index)
        if self._stacked_widget.currentWidget() == self.magicbox:
            self.magicbox.setFocus()

    def _on_stack_switch_toggled(self, checked):
        if checked:
            self._stack_switch.setToolTip("关闭搜索框")
        else:
            self._stack_switch.setToolTip("显示搜索框")

    def _on_stacked_widget_changed(self, _):
        self._stack_switch.setChecked(
            self._stacked_widget.currentWidget() == self.magicbox
        )

    def add_stacked_widget(self, widget):
        """

        .. versionadded:: 3.7.10
        """
        self._stacked_widget.addWidget(widget)
        if self._stacked_widget.count() > 1:
            self._stack_switch.show()

    def set_top_stacked_widget(self, widget):
        """

        .. versionadded:: 3.7.10
        """
        self._stacked_widget.setCurrentWidget(widget)

    def clear_stacked_widget(self):
        """

        .. versionadded:: 3.7.10
        """
        while self._stacked_widget.count() > 0:
            self._stacked_widget.removeWidget(self._stacked_widget.currentWidget())
        self._stack_switch.hide()

    def show_and_focus_magicbox(self):
        """Show and focus magicbox

        .. versionadded:: 3.7.10
        """
        if self._stacked_widget.indexOf(self.magicbox) != -1:
            self.set_top_stacked_widget(self.magicbox)
            self.magicbox.setFocus()
