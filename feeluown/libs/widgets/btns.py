# -*- coding: utf-8 -*-

from .base import FButton


class _MultiSwitchButton(FButton):
    def __init__(self, app, index=[], states=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app
        self.index = index
        self.states = states

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        pass
