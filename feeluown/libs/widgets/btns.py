# -*- coding: utf-8 -*-

from .base import FButton


class _MultiSwitchButton(FButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
