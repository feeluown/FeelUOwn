# -*- coding=utf8 -*-

from enum import Enum

from Xlib.display import Display
from Xlib import X
from Xlib.ext import record
from Xlib.protocol import rq

from feeluown.logger import LOG
from feeluown.controller_api import ControllerApi


__author__ = 'cosven'

"""
0x1008ff17 media_next
0x1008ff16 media_previous
0x1008ff15 media_stop
0x1008ff14 media_play_pause
"""


class MediaKey(Enum):
    media_next = "0x1008ff17"
    media_previous = "0x1008ff16"
    media_stop = "0x1008ff15"
    media_play_pause = "0x1008ff14"


class KeyEventLoop(object):
    def __init__(self):
        self.disp = Display()
        self.root = self.disp.screen().root

    def handler(self, reply):
        """ This function is called when a xlib event is fired """
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(
                data, self.disp.display, None, None)

            if event.type == X.KeyPress:
                pass
            elif event.type == X.KeyRelease:
                keycode = event.detail
                keysym = self.disp.keycode_to_keysym(keycode, 0)
                if hex(keysym) == MediaKey.media_next.value:
                    ControllerApi.player.play_next()
                elif hex(keysym) == MediaKey.media_previous.value:
                    ControllerApi.player.play_last()
                elif hex(keysym) == MediaKey.media_stop.value:
                    ControllerApi.player.stop()
                elif hex(keysym) == MediaKey.media_play_pause.value:
                    ControllerApi.player.play_or_pause()

    def run(self):
        # Monitor keypress and button press
        LOG.info("Linux multimedia hotkey start")
        ctx = self.disp.record_create_context(
            0,
            [record.AllClients],
            [{
                'core_requests': (0, 0),
                'core_replies': (0, 0),
                'ext_requests': (0, 0, 0, 0),
                'ext_replies': (0, 0, 0, 0),
                'delivered_events': (0, 0),
                'device_events': (X.KeyReleaseMask, X.ButtonReleaseMask),
                'errors': (0, 0),
                'client_started': False,
                'client_died': False,
            }])
        self.disp.record_enable_context(ctx, self.handler)
        self.disp.record_free_context(ctx)

        while 1:
            # Infinite wait, doesn't do anything as no events are grabbed
            event = self.root.display.next_event()


if __name__ == "__main__":
    e = KeyEventLoop()
    e.run()
