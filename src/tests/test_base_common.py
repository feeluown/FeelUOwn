# -*- coding: utf8 -*-


import pytest

from base.common import *


def test_singleton():
    @singleton
    class A():
        def __init__(self):
            pass
    a1 = A()
    a2 = A()
    assert id(a1) == id(a2)
