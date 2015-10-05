# -*- coding: utf-8 -*-

from _thread import start_new_thread

from .socket_server import Server


def init():
    start_new_thread(Server.start, ())
