# -*- coding: utf-8 -*-

from .base import FLabel


class _BasicLabel(FLabel):
    '''label with basic style'''
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        theme = app.theme_manager.current_theme
        self._style_str = '''
            QLabel {{
                background: transparent;
                color: {0};
            }}
        '''.format(theme.foreground.name())
        self.set_theme_style()

    def set_theme_style(self):
        self.setStyleSheet(self._style_str)
