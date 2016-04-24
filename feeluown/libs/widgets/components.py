# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout

from .base import FFrame, FLabel


class LP_GroupHeader(FFrame):
    def __init__(self, app, title=None, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.title_label = FLabel(title, self)

        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        pass

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.title_label)


class LP_GroupItem(FFrame):
    def __init__(self, app, name=None, parent=None):
        super().__init__(parent)

        self._layout = QHBoxLayout(self)
        self._flag_label = FLabel(self)
        self._name_label = FLabel(name, self)

        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        pass

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self._flag_label)
        self._layout.addWidget(self._name_label)


class LP_Group(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QVBoxLayout(self)
        self.header = LP_GroupHeader(self._app, self)

        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        pass

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.header)
