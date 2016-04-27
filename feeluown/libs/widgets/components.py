# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QHBoxLayout

from .base import FFrame, FLabel


class LP_GroupHeader(FFrame):
    def __init__(self, app, title=None, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.title_label = FLabel(title, self)
        self.title_label.setIndent(8)

        self.setObjectName('lp_group_header')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}

            #{0} QLabel {{
                font-size: 12px;
                color: {1};
            }}
        '''.format(self.objectName(),
                   theme.foreground_light.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setFixedHeight(22)

        self._layout.addWidget(self.title_label)

    def set_header(self, text):
        self.title_label.setText(text)


class LP_GroupItem(FFrame):
    def __init__(self, app, name=None, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self._flag_label = FLabel(self)
        self._img_label = FLabel(self)
        self._name_label = FLabel(name, self)

        self.setObjectName('lp_group_item')
        self._flag_label.setObjectName('lp_groun_item_flag')
        self._flag_label.setText('➣')
        self._flag_label.setIndent(5)
        self._img_label.setObjectName('lp_group_item_img')
        self._img_label.setText('♬')
        self._name_label.setObjectName('lp_group_item_name')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
            #{3} {{
                color: {4};
                font-size: 13px;
            }}
            #{1} {{
                color: transparent;
                font-size: 14px;
            }}
            #{2} {{
                color: {4};
                font-size: 14px;
            }}
        '''.format(self.objectName(),
                   self._flag_label.objectName(),
                   self._img_label.objectName(),
                   self._name_label.objectName(),
                   theme.foreground.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setFixedHeight(26)
        self._img_label.setFixedWidth(18)
        self._flag_label.setFixedWidth(22)

        self._layout.addWidget(self._flag_label)
        self._layout.addWidget(self._img_label)
        self._layout.addSpacing(2)
        self._layout.addWidget(self._name_label)

    def set_focus(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
            #{1} {{
                color: {4};
                font-size: 14px;
            }}
            #{2} {{
                color: {5};
                font-size: 14px;
            }}
            #{3} {{
                color: {6};
                font-size: 13px;
            }}
        '''.format(self.objectName(),
                   self._flag_label.objectName(),
                   self._img_label.objectName(),
                   self._name_label.objectName(),
                   theme.color5_light.name(),
                   theme.color6.name(),
                   theme.color3_light.name())
        self.setStyleSheet(style_str)
