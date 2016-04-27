# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QStyleOption, QStyle

from .consts import DEFAULT_THEME_NAME
from .ui import Ui
from .theme import ThemeManager
from .plugin import PluginsManager
from feeluown.libs.widgets.base import FWidget


class App(FWidget):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager(self)
        self.plugins_manager = PluginsManager(self)
        self.theme_manager.set_theme(DEFAULT_THEME_NAME)

        self.ui = Ui(self)

        self._init_managers()

        self.resize(960, 600)
        self.setObjectName('app')
        self.set_theme_style()

        self.test()

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def _init_managers(self):
        self.plugins_manager.scan()

    def set_theme_style(self):
        theme = self.theme_manager.current_theme
        style_str = '''
            #app {{
                background: {0};
                color: {1};
            }}
        '''.format(theme.background.name(),
                   theme.foreground.name())
        self.setStyleSheet(style_str)

    def test(self):
        # self.theme_manager.choose('')
        pass
