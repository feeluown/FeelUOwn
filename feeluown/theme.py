# -*- coding: utf-8 -*-

import os
import logging
import configparser

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor

from .consts import THEMES_DIR, USER_THEMES_DIR


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
            if hasattr(widget, 'set_theme_style'):
                widget.set_theme_style()
            for child in widget.children():
                if isinstance(child, QWidget):
                    recursive_update(child)

        self.set_theme(theme_name)
        recursive_update(self._app)

    def scan(self, themes_dir=[THEMES_DIR, USER_THEMES_DIR]):
        '''themes directory'''
        self._themes = []
        for directory in themes_dir:
            files = os.listdir(directory)
            for f in files:
                f_name, f_ext = f.split('.')
                if f_ext == 'colorscheme':
                    self._themes.append(f_name)

    def list(self):
        '''show themes list

        :param theme: theme unique name
        :return: themes name list
        '''
        if not self._themes:
            self.scan()
        return self._themes

    def get_theme(self, theme_name):
        '''
        :param theme: unique theme name
        :return: `Theme` object
        '''
        pass

    def set_theme(self, theme_name):
        '''set current theme'''
        self.current_theme = Theme(theme_name)


class Theme(object):
    def __init__(self, config_name=None):
        self._config = configparser.ConfigParser()
        self.name = config_name

        self.read(config_name)

    def read(self, config_file):
        if config_file is not None:
            config_file_path = os.path.abspath(THEMES_DIR + '/' + config_file +
                                               '.colorscheme')
            if not os.path.exists(config_file_path):
                config_file_path = os.path.abspath(
                    USER_THEMES_DIR + '/' + config_file + '.colorscheme')
                print('........ %s ............' % config_file_path)
            config = self._config.read(config_file_path)
            if config:
                return True
        return False

    @property
    def background_light(self):
        color_section = self._config['Background']
        return self._parse_color_str(color_section['color'])

    @property
    def background(self):
        color_section = self._config['BackgroundIntense']
        return self._parse_color_str(color_section['color'])

    @property
    def foreground_light(self):
        color_section = self._config['Foreground']
        return self._parse_color_str(color_section['color'])

    @property
    def foreground(self):
        color_section = self._config['ForegroundIntense']
        return self._parse_color_str(color_section['color'])

    @property
    def color0_light(self):
        color_section = self._config['Color0']
        return self._parse_color_str(color_section['color'])

    @property
    def color0(self):
        color_section = self._config['Color0Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color1_light(self):
        color_section = self._config['Color1']
        return self._parse_color_str(color_section['color'])

    @property
    def color1(self):
        color_section = self._config['Color1Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color2_light(self):
        color_section = self._config['Color2']
        return self._parse_color_str(color_section['color'])

    @property
    def color2(self):
        color_section = self._config['Color2Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color3_light(self):
        color_section = self._config['Color3']
        return self._parse_color_str(color_section['color'])

    @property
    def color3(self):
        color_section = self._config['Color3Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color4_light(self):
        color_section = self._config['Color4']
        return self._parse_color_str(color_section['color'])

    @property
    def color4(self):
        color_section = self._config['Color4Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color5_light(self):
        color_section = self._config['Color5']
        return self._parse_color_str(color_section['color'])

    @property
    def color5(self):
        color_section = self._config['Color5Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color6_light(self):
        color_section = self._config['Color6']
        return self._parse_color_str(color_section['color'])

    @property
    def color6(self):
        color_section = self._config['Color6Intense']
        return self._parse_color_str(color_section['color'])

    @property
    def color7_light(self):
        color_section = self._config['Color7']
        return self._parse_color_str(color_section['color'])

    @property
    def color7(self):
        color_section = self._config['Color7Intense']
        return self._parse_color_str(color_section['color'])

    def _parse_color_str(self, color_str):
        rgb = [int(x) for x in color_str.split(',')]
        return QColor(rgb[0], rgb[1], rgb[2])
