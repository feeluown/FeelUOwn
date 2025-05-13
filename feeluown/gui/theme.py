# -*- coding: utf-8 -*-

from __future__ import annotations
import logging
import json
import os
from collections import defaultdict
from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QGuiApplication, QPalette, QColor
from feeluown.gui.helpers import get_qapp

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


Dark = DARK = 'dark'
Light = LIGHT = 'light'
MacOSDark = 'macos_dark'  # for Linux/Windows Users

Roles = ['AlternateBase', 'Background', 'Base', 'BrightText',
         'Button', 'ButtonText', 'Dark', 'Foreground', 'Highlight',
         'HighlightedText', 'Light', 'Link', 'LinkVisited', 'Mid',
         'Midlight', 'NoRole', 'PlaceholderText', 'Shadow', 'Text',
         'ToolTipBase', 'ToolTipText', 'Window', 'WindowText']

Groups = ['Disabled', 'Active', 'Inactive']


def read_resource(filename):
    filepath = os.path.abspath(__file__)
    dirname = os.path.dirname(filepath)
    qssfilepath = os.path.join(dirname, 'assets/themes/{}'.format(filename))
    with open(qssfilepath, encoding='UTF-8') as f:
        s = f.read()
    return s


class ThemeManager(QObject):
    """colors/icons manager"""

    theme_changed = pyqtSignal(str)

    def __init__(self, app: GuiApp, parent=None):
        super().__init__(parent=parent)
        self._app = app
        self.theme = None

    def initialize(self):
        # XXX: I don't know why we should autoload twice
        # to make it work well on Linux(GNOME)
        self.autoload()
        self._app.started.connect(lambda app: self.autoload(), weak=False)
        get_qapp().paletteChanged.connect(self.on_palette_changed)

    def on_palette_changed(self, p: QPalette):
        if self._app.config.THEME == 'auto':
            theme = self.guess_theme_by_palette(p)
            self.load_theme(theme)

    def autoload(self):
        if self._app.config.THEME == 'auto':
            theme = self.guess_system_theme()
        else:  # user settings have highest priority
            theme = self._app.config.THEME
        self.load_theme(theme)

    def load_theme(self, theme):
        if theme == DARK:
            self.load_dark()
        elif theme == MacOSDark:
            self.load_macos_dark()
        else:
            self.load_light()
        self.theme = theme
        self.theme_changed.emit(theme)

    def guess_theme_by_palette(self, palette):
        bg_color = palette.color(QPalette.Window)
        if bg_color.lightness() > 150:
            return LIGHT
        return DARK

    def guess_system_theme(self):
        palette = self._app.palette()
        return self.guess_theme_by_palette(palette)

    def load_light(self):
        common = read_resource('common.qss')
        light = read_resource('light.qss')
        get_qapp().setStyleSheet(common + light)

    def load_dark(self):
        common = read_resource('common.qss')
        dark = read_resource('dark.qss')
        get_qapp().setStyleSheet(common + dark)

    def load_macos_dark(self):
        """
        So many DEs on Linux! Hard to compat! We give them macOS
        dark theme colors!

        Users can also design a theme colors by themselves,
        we provider dump_colors/load_colors function for conviniece.
        """
        self.load_dark()
        content = read_resource('macos_dark.colors')
        colors = json.loads(content)
        try:
            get_qapp().paletteChanged.disconnect(self.autoload)
        except TypeError:
            pass
        palette = load_colors(colors)
        self._app.setPalette(palette)
        get_qapp().paletteChanged.connect(self.autoload)

    def get_pressed_color(self):
        """pressed color for button-like widget

        In Feeluown, we have two kinds of buttons, text and icon. All TextButtons
        have same color in pressed state.

        THINKING: we can create a API for theme manager like QPalette.color if we need
        """
        if self.guess_system_theme() == DARK:
            return '#3e3e3e'
        return '#DDD'

    def get_icon(self, name):
        """get icon by name

        this API is similar to QIcon.fromTheme
        """
        theme_kind = self.guess_system_theme()
        if name == 'tray':
            if theme_kind == DARK:
                return 'icons:tray-dark.png'
            return 'icons:tray-light.png'


def dump_colors():
    json_ = defaultdict(dict)  # type: ignore[var-annotated]
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
