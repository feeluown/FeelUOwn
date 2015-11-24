# -*- coding=utf8 -*-
__author__ = 'cosven'

from base.logger import LOG


def run_event_loop(player):
    import Quartz
    from AppKit import NSKeyUp, NSSystemDefined, NSEvent

    def keyboard_tap_callback(proxy, type_, event, refcon):
        if type_ < 0 or type_ > 0x7fffffff:
            LOG.error('Unkown mac event')
            Quartz.CFRunLoopRun()
            return None
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
        # NSSystemDefined for media keys
        Quartz.CGEventMaskBit(NSSystemDefined),
        keyboard_tap_callback,
        None
    )

    run_loop_source = Quartz.CFMachPortCreateRunLoopSource(
        Quartz.kCFAllocatorDefault, tap, 0)
    Quartz.CFRunLoopAddSource(
        Quartz.CFRunLoopGetCurrent(),
        run_loop_source,
        Quartz.kCFRunLoopDefaultMode
    )
    # Enable the tap
    Quartz.CGEventTapEnable(tap, True)
    # and run! This won't return until we exit or are terminated.
    Quartz.CFRunLoopRun()
    LOG.error('Mac hotkey exit event ')
