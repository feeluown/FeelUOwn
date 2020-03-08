# -*- coding: utf-8 -*-

import logging
import json
import os
import sys
from collections import defaultdict

from PyQt5.QtGui import QGuiApplication, QPalette, QColor
from PyQt5.QtWidgets import QApplication
from fuocore.utils import is_osx, get_osx_theme

logger = logging.getLogger(__name__)


DARK = 'dark'
LIGHT = 'light'

Roles = ['AlternateBase', 'Background', 'Base', 'BrightText',
         'Button', 'ButtonText', 'Dark', 'Foreground', 'Highlight',
         'HighlightedText', 'Light', 'Link', 'LinkVisited', 'Mid',
         'Midlight', 'NoRole', 'PlaceholderText', 'Shadow', 'Text',
         'ToolTipBase', 'ToolTipText', 'Window', 'WindowText']

Groups = ['Disabled', 'Active', 'Inactive']


def read_resource(filename):
    filepath = os.path.abspath(__file__)
    dirname = os.path.dirname(filepath)
    qssfilepath = os.path.join(dirname, 'themes/{}'.format(filename))
    with open(qssfilepath, encoding='UTF-8') as f:
        s = f.read()
    return s


class ThemeManager:
    """检测系统主题，自动适配

    **TODO**:

    - 添加 dark 主题
    - 检测系统主题
    """
    def __init__(self, app):
        self._app = app
        self.theme = None

    def initialize(self):
        # XXX: I don't know why we should autoload twice
        # to make it work well on Linux(GNOME)
        self.autoload()
        self._app.initialized.connect(lambda app: self.autoload(), weak=False)
        QApplication.instance().paletteChanged.connect(self.autoload)

    def autoload(self):
        if self._app.config.THEME == 'auto':
            if is_osx():
                if get_osx_theme() == 1:
                    theme = DARK
                else:
                    theme = LIGHT
            else:
                theme = self.guess_system_theme()
        else:  # user settings have highest priority
            theme = self._app.config.THEME

        if theme == DARK:
            self.load_dark()
        else:
            self.load_light()

        self.theme = theme

    def guess_system_theme(self):
        palette = self._app.palette()
        bg_color = palette.color(QPalette.Window)
        if bg_color.lightness() > 150:
            return LIGHT
        return DARK

    def load_light(self):
        common = read_resource('common.qss')
        light = read_resource('light.qss')
        QApplication.instance().setStyleSheet(common + light)

    def load_dark(self):
        common = read_resource('common.qss')
        dark = read_resource('dark.qss')
        QApplication.instance().setStyleSheet(common + dark)

        if sys.platform.lower() == 'linux':
            # So many DEs on Linux! Hard to compat! We give them macOS
            # dark theme colors!
            #
            # Users can also design a theme colors by themselves,
            # we provider dump_colors/load_colors function for conviniece.
            content = read_resource('macos_dark.colors')
            colors = json.loads(content)
            try:
                QApplication.instance().paletteChanged.disconnect(self.autoload)
            except TypeError:
                pass
            palette = load_colors(colors)
            self._app.setPalette(palette)
            QApplication.instance().paletteChanged.connect(self.autoload)


def dump_colors():
    json_ = defaultdict(dict)
    palette = QGuiApplication.palette()
    for group_attr in Groups:
        group = getattr(QPalette, group_attr)
        for role_attr in Roles:
            role = getattr(QPalette, role_attr)
            json_[group_attr][role_attr] = palette.color(group, role).name()
    return json_


def load_colors(colors):
    palette = QGuiApplication.palette()
    for group_attr, value in colors.items():
        for role_attr, color_name in value.items():
            try:
                role = getattr(QPalette, role_attr)
                group = getattr(QPalette, group_attr)
                palette.setColor(group, role, QColor(color_name))
            except AttributeError:
                pass
    QGuiApplication.setPalette(palette)
    return palette
