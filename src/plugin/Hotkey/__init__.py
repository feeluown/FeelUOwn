# -*- coding:utf8 -*-

import sys
import asyncio
from base.logger import LOG


def init(controller):
    if sys.platform == "darwin":
        player = controller.player
        APP_EVENT_LOOP = asyncio.get_event_loop()
        APP_EVENT_LOOP.call_later(1, run_event_loop, player)


def run_event_loop(player):
    import Quartz
    from AppKit import NSKeyUp, NSSystemDefined, NSEvent

    def keyboard_tap_callback(proxy, type_, event, refcon):
        try:
            key_event = NSEvent.eventWithCGEvent_(event)
        except:
            LOG.info("mac event cast error")
            return event
        if key_event.subtype() == 8:
            key_code = (key_event.data1() & 0xFFFF0000) >> 16
            key_state = (key_event.data1() & 0xFF00) >> 8
            if key_code is 16 or key_code is 19 or key_code is 20:
                # 16 for play-pause, 19 for next, 20 for previous
                if key_state == NSKeyUp:
                    if key_code is 19:
                        player.play_next()
                    elif key_code is 20:
                        player.play_last()
                    elif key_code is 16:
                        player.play_or_pause()
                return None
        return event

    # Set up a tap, with type of tap, location, options and event mask
    tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap,  # Session level is enough for our needs
        Quartz.kCGHeadInsertEventTap,  # Insert wherever, we do not filter
        Quartz.kCGEventTapOptionDefault,
        Quartz.CGEventMaskBit(NSSystemDefined),  # NSSystemDefined for media keys
        keyboard_tap_callback,
        None
    )

    run_loop_source= Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
    Quartz.CFRunLoopAddSource(
        Quartz.CFRunLoopGetCurrent(),
        run_loop_source,
        Quartz.kCFRunLoopDefaultMode
    )
    # Enable the tap
    Quartz.CGEventTapEnable(tap, True)
    # and run! This won't return until we exit or are terminated.
    Quartz.CFRunLoopRun()