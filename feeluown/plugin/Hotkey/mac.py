# -*- coding=utf8 -*-

import asyncio

from feeluown.logger import LOG
from feeluown.controller_api import ControllerApi

__author__ = 'cosven'


def keyboard_tap_callback(proxy, type_, event, refcon):
        from AppKit import NSKeyUp, NSEvent, NSBundle
        NSBundle.mainBundle().infoDictionary()['NSAppTransportSecurity'] =\
            dict(NSAllowsArbitraryLoads=True)
        if type_ < 0 or type_ > 0x7fffffff:
            LOG.error('Unkown mac event')
            run_event_loop()
            LOG.error('restart mac key board event loop')
            return event
        try:
            key_event = NSEvent.eventWithCGEvent_(event)
        except:
            LOG.info("mac event cast error")
            return event
        if key_event.subtype() == 8:
            key_code = (key_event.data1() & 0xFFFF0000) >> 16
            key_state = (key_event.data1() & 0xFF00) >> 8
            if key_code in (16, 19, 20):
                # 16 for play-pause, 19 for next, 20 for previous
                if key_state == NSKeyUp:
                    if key_code is 19:
                        ControllerApi.player.play_next()
                    elif key_code is 20:
                        ControllerApi.player.play_last()
                    elif key_code is 16:
                        ControllerApi.player.play_or_pause()
                return None
        return event


def run_event_loop():
    LOG.info("try to load mac hotkey event loop")
    import Quartz
    from AppKit import NSSystemDefined

    # Set up a tap, with type of tap, location, options and event mask
    tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap,  # Session level is enough for our needs
        Quartz.kCGHeadInsertEventTap,  # Insert wherever, we do not filter
        Quartz.kCGEventTapOptionDefault,
        # NSSystemDefined for media keys
        Quartz.CGEventMaskBit(NSSystemDefined),
        keyboard_tap_callback,
        None
    )

    run_loop_source = Quartz.CFMachPortCreateRunLoopSource(
        None, tap, 0)
    Quartz.CFRunLoopAddSource(
        Quartz.CFRunLoopGetCurrent(),
        run_loop_source,
        Quartz.kCFRunLoopDefaultMode
    )
    # Enable the tap
    Quartz.CGEventTapEnable(tap, True)
    # and run! This won't return until we exit or are terminated.
    Quartz.CFRunLoopRun()
    LOG.error('Mac hotkey event loop exit')
    return []


@asyncio.coroutine
def run():
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, run_event_loop)
    yield from future
