# -*- coding: utf-8 -*-

import os
import logging
from enum import Enum
import configparser

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor

from .consts import THEMES_DIR


logger = logging.getLogger(__name__)


class ThemeManager(object):
    def __init__(self, app):
        super().__init__()
        self._app = app

        self.current_theme = None
        self._themes = []    # config file name (theme name)

    def choose(self, theme_name):
        '''
        :param theme: theme unique name
        '''
        def recursive_update(widget):
            widget.set_theme_style()
            for child in widget.children():
                if isinstance(child, QWidget) and \
                        hasattr(child, 'set_theme_style'):
                    child.set_theme_style()
                    recursive_update(child)

        self.set_theme(theme_name)
        recursive_update(self._app)

    def scan(self, themes_dir):
        '''themes directory'''
        pass

    def list(self):
        '''show themes list

        :param theme: theme unique name
        :return: themes name list
        '''
        pass

    def get_theme(self, theme_name):
        '''
        :param theme: unique theme name
        :return: `Theme` object
        '''
        pass

    def set_theme(self, theme_name):
        '''set current theme'''
        self.current_theme = Theme(theme_name)


class ThemeMode(Enum):
    dark = 0
    light = 1


class Theme(object):
    def __init__(self, config_file=None):
        self.current_mode = ThemeMode.dark
        self._config = configparser.ConfigParser()

        self.read(config_file)

    def read(self, config_file):
        config_file_path = os.path.abspath(THEMES_DIR + config_file +
                                           '.colorscheme')
        if config_file is not None:
            config = self._config.read(config_file_path)
            if config:
                return True
        return False

    def change_mode(self):
        '''change between dark and light'''
        if self.current_mode == ThemeMode.dark:
            self.current_mode = ThemeMode.light
        else:
            self.current_mode = ThemeMode.dark

    @property
    def background(self):
        if self.current_mode == ThemeMode.light:
            color_section = self._config['Background']
        else:
            color_section = self._config['BackgroundIntense']
        return self._parse_color_str(color_section['color'])

    @property
    def foreground(self):
        if self.current_mode == ThemeMode.light:
            color_section = self._config['Foreground']
        else:
            color_section = self._config['ForegroundIntense']
        return self._parse_color_str(color_section['color'])

    @property
    def color0(self):
        '''relative black'''
        if self.current_mode == ThemeMode.light:
            color_section = self._config['Color0']
        else:
            color_section = self._config['Color0Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color1(self):
        '''relative red'''
        if self.current_mode == ThemeMode.light:
            color_section = self._config['Color1']
        else:
            color_section = self._config['Color1Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color2(self):
        '''relative green'''
        if self.current_mode == ThemeMode.light:
            color_section = self._config['Color2']
        else:
            color_section = self._config['Color2Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color3(self):
        '''relative yellow'''
        if self.current_mode == ThemeMode.light:
            color_section = self._config['Color3']
        else:
            color_section = self._config['Color3Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color4(self):
        '''relative blue'''
        if self.current_mode == ThemeMode.light:
            color_section = self._config['Color4']
        else:
            color_section = self._config['Color4Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color5(self):
        '''relative magenta'''
        if self.current_mode == ThemeMode.light:
            color_section = self._config['Color5']
        else:
            color_section = self._config['Color5Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color6(self):
        '''relative cyan'''
        if self.current_mode == ThemeMode.light:
            color_section = self._config['Color6']
        else:
            color_section = self._config['Color6Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color7(self):
        '''relative white'''
        if self.current_mode == ThemeMode.light:
            color_section = self._config['Color7']
        else:
            color_section = self._config['Color7Intense']
        return self._parse_color_str(color_section['color'])

    def _parse_color_str(self, color_str):
        rgb = [int(x) for x in color_str.split(',')]
        return QColor(rgb[0], rgb[1], rgb[2])
