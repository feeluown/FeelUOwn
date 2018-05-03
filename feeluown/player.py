# -*- coding: utf-8 -*-
import locale
import logging

from fuocore.core.player import MpvPlayer


logger = logging.getLogger(__name__)


class Player(MpvPlayer):

    def __init__(self):
        locale.setlocale(locale.LC_NUMERIC, 'C')
        super().__init__()
        self.initialize()
