from enum import Enum

from Xlib.display import Display
from Xlib import X
from Xlib.ext import record
from Xlib.protocol import rq

"""
0x1008ff17 media_next
0x1008ff16 media_previous
0x1008ff15 media_stop
0x1008ff14 media_play_pause
"""


disp = None


class MediaKey(Enum):
    media_next = "0x1008ff17"
    media_previous = "0x1008ff16"
    media_stop = "0x1008ff15"
    media_play_pause = "0x1008ff14"


def handler(reply):
    """ This function is called when a xlib event is fired """
    data = reply.data
    while len(data):
        event, data = rq.EventField(None).parse_binary_value(
            data, disp.display, None, None)

        if event.type == X.KeyPress:
            pass
        elif event.type == X.KeyRelease:
            keycode = event.detail
            keysym = disp.keycode_to_keysym(keycode, 0)
            if hex(keysym) == MediaKey.media_next.value:
                print("next")
            elif hex(keysym) == MediaKey.media_previous.value:
                print("previous")
            elif hex(keysym) == MediaKey.media_stop.value:
                print("stop")
            elif hex(keysym) == MediaKey.media_play_pause.value:
                print("play_or_pause")

# get current display
disp = Display()
root = disp.screen().root

# Monitor keypress and button press
ctx = disp.record_create_context(
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
disp.record_enable_context(ctx, handler)
disp.record_free_context(ctx)

while 1:
    # Infinite wait, doesn't do anything as no events are grabbed
    event = root.display.next_event()

