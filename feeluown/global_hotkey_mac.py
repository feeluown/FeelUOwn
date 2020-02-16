# -*- coding=utf8 -*-

import logging
import socket
import threading

import Quartz
from AppKit import NSSystemDefined
from AppKit import NSKeyUp, NSEvent, NSBundle

logger = logging.getLogger(__name__)


def send_cmd(cmd):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 23333))
    sock.recv(1024)
    sock.sendall(bytes(cmd, 'utf-8') + b'\n')
    sock.close()


def keyboard_tap_callback(proxy, type_, event, refcon):
    NSBundle.mainBundle().infoDictionary()['NSAppTransportSecurity'] =\
        dict(NSAllowsArbitraryLoads=True)
    if type_ < 0 or type_ > 0x7fffffff:
        logger.error('Unkown mac event')
        run_event_loop()
        logger.error('restart mac key board event loop')
        return event
    try:
        # 这段代码如果运行在非主线程，它会有如下输出，根据目前探索，
        # 这并不影响它的运行，我们暂时可以忽略它。
        # Python pid(11)/euid(11) is calling TIS/TSM in non-main thread environment.
        # ERROR : This is NOT allowed.
        key_event = NSEvent.eventWithCGEvent_(event)
    except:  # noqa
        logger.info("mac event cast error")
        return event
    if key_event.subtype() == 8:
        key_code = (key_event.data1() & 0xFFFF0000) >> 16
        key_state = (key_event.data1() & 0xFF00) >> 8
        if key_code in (16, 19, 20):
            # 16 for play-pause, 19 for next, 20 for previous
            if key_state == NSKeyUp:
                if key_code == 19:
                    logger.info('mac hotkey: play next')
                    send_cmd('next')
                elif key_code == 20:
                    logger.info('mac hotkey: play last')
                    send_cmd('previous')
                elif key_code == 16:
                    logger.info('mac hotkey: toggle')
                    send_cmd('toggle')
            return None
    return event


def run_event_loop():
    logger.info('try to load mac hotkey event loop')
    # Set up a tap, with type of tap, location, options and event mask

    def create_tap():
        return Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,  # Session level is enough for our needs
            Quartz.kCGHeadInsertEventTap,  # Insert wherever, we do not filter
            Quartz.kCGEventTapOptionDefault,
            # NSSystemDefined for media keys
            Quartz.CGEventMaskBit(NSSystemDefined),
            keyboard_tap_callback,
            None
        )
    tap = create_tap()
    if tap is None:
        logger.error('Error occurred when trying to listen global hotkey. '
                     'trying to popup a prompt dialog to ask for permission.')
        # we do not use pyobjc-framework-ApplicationServices directly, since it
        # causes segfault when call AXIsProcessTrustedWithOptions function
        import objc
        AS = objc.loadBundle('CoreServices', globals(),
                             '/System/Library/Frameworks/ApplicationServices.framework')
        objc.loadBundleFunctions(AS, globals(),
                                 [('AXIsProcessTrustedWithOptions', b'Z@')])
        objc.loadBundleVariables(AS, globals(),
                                 [('kAXTrustedCheckOptionPrompt', b'@')])
        trusted = AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})  # noqa
        if not trusted:
            logger.info('Have popuped a prompt dialog to ask for accessibility.'
                        'You can restart feeluown after you grant access to it.')
        else:
            logger.warning('Have already grant accessibility, '
                           'but we still can not listen global hotkey,'
                           'theoretically, this should not happen.')
        return

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
    logger.error('mac hotkey event loop exit')
    return []


class MacGlobalHotkeyManager:

    def __init__(self):
        self._t = None
        self._started = False

    def start(self):
        # mac event loop 最好运行在主线程中，但是测试发现它也可以运行
        # 在非主线程。但不能运行在子进程中。
        self._t = threading.Thread(
            target=run_event_loop,
            name='MacGlobalHotkeyListener'
        )
        self._t.daemon = True
        self._t.start()
        self._started = True

    def stop(self):
        # FIXME: 经过测试发现，这个 stop 函数并不会正常工作。
        # 现在是将 thread 为 daemon thread，让线程在程序退出时停止。
        if self._started:
            loop = Quartz.CFRunLoopGetCurrent()
            Quartz.CFRunLoopStop(loop)
            self._t.join()
