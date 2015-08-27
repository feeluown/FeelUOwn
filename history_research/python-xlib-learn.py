from Xlib.display import Display
from Xlib import X
from Xlib.ext import record
from Xlib.protocol import rq

disp = None

def handler(reply):
    """ This function is called when a xlib event is fired """
    data = reply.data
    while len(data):
        event, data = rq.EventField(None).parse_binary_value(data, disp.display, None, None)

        # KEYCODE IS FOUND USERING event.detail
        print(event.detail)

        if event.type == X.KeyPress:
            # BUTTON PRESSED
            print("pressed")
        elif event.type == X.KeyRelease:
            # BUTTON RELEASED
            print("released")

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
