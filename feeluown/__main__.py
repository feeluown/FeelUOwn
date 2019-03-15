#! /usr/bin/env python3

import argparse
import asyncio
import logging
import os

import traceback
import sys

from fuocore import __version__ as fuocore_version
from fuocore.dispatch import Signal
from fuocore.utils import is_port_used

from feeluown.app import App, create_app
from feeluown.cli import main as climain, print_error
from feeluown import logger_config, __version__ as feeluown_version
from feeluown.consts import (
    HOME_DIR, USER_PLUGINS_DIR, DATA_DIR,
    CACHE_DIR, USER_THEMES_DIR, SONG_DIR, COLLECTIONS_DIR
)
from feeluown.rcfile import load_rcfile, bind_signals

logger = logging.getLogger(__name__)


def ensure_dirs():
    for d in (HOME_DIR, DATA_DIR,
              USER_THEMES_DIR, USER_PLUGINS_DIR,
              CACHE_DIR, SONG_DIR, COLLECTIONS_DIR):
        if not os.path.exists(d):
            os.mkdir(d)


def excepthook(exc_type, exc_value, tb):
    """Exception hook"""
    src_tb = tb
    while src_tb.tb_next:
        src_tb = src_tb.tb_next
    logger.error('Exception occured: print locals varibales')
    logger.error(src_tb.tb_frame.f_locals)
    traceback.print_exception(exc_type, exc_value, tb)


def create_config():
    from feeluown.config import Config
    config = Config()
    config.deffield('DEBUG', type_=bool, desc='是否为调试模式')
    config.deffield('MODE', desc='CLI or GUI 模式')
    config.deffield('MPV_AUDIO_DEVICE', default='auto', desc='MPV 播放设备')
    config.deffield('COLLECTIONS_DIR',  desc='本地收藏所在目录')
    config.deffield('FORCE_MAC_HOTKEY', desc='强制开启 macOS 全局快捷键功能')
    return config


def check_daemon_started():
    if is_port_used(23333) or is_port_used(23334):
        return True
    return False


def map_args_to_config(args, config):
    config.DEBUG = args.debug
    config.MPV_AUDIO_DEVICE = args.mpv_audio_device
    config.MODE = App.CliMode if args.no_window else (App.GuiMode | App.CliMode)
    config.FORCE_MAC_HOTKEY = args.force_mac_hotkey


def setup_argparse():
    parser = argparse.ArgumentParser(description='运行 FeelUOwn 播放器')
    subparsers = parser.add_subparsers(description='客户端命令', dest='cmd')

    play_parser = subparsers.add_parser('play')
    show_parser = subparsers.add_parser('show')
    search_parser = subparsers.add_parser('search')

    pause_parser = subparsers.add_parser('pause')
    resume_parser = subparsers.add_parser('resume')
    toggle_parser = subparsers.add_parser('toggle')
    stop_parser = subparsers.add_parser('stop')
    next_parser = subparsers.add_parser('next')
    previous_parser = subparsers.add_parser('previous')
    list_parser = subparsers.add_parser('list')
    clear_parser = subparsers.add_parser('clear')
    remove_parser = subparsers.add_parser('remove')
    status_parser = subparsers.add_parser('status')
    exec_parser = subparsers.add_parser('exec')

    play_parser.add_argument('uri', help='歌曲 uri')
    show_parser.add_argument('uri', help='显示资源详细信息')
    remove_parser.add_argument('uri', help='从播放列表移除歌曲')
    search_parser.add_argument('keyword', help='搜索关键字')
    exec_parser.add_argument('code', help='Python 代码')

    parser.add_argument('--daemon', action='store_true', default=True,
                        help='在后台运行')
    parser.add_argument('-nw', '--no-window', action='store_true', default=False,
                        help='不显示 GUI 窗口')

    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='开启调试模式')
    parser.add_argument('-v', '--version', action='store_true',
                        help='显示当前 feeluown 和 fuocore 版本')
    parser.add_argument('--log-to-file', action='store_true', default=False,
                        help='将日志打到文件中')
    parser.add_argument('--force-mac-hotkey', action='store_true', default=False,
                        help='强制开启 mac 全局热键')
    # XXX: 不知道能否加一个基于 regex 的 option？比如加一个
    # `--mpv-*` 的 option，否则每个 mpv 配置我都需要写一个 option？

    # TODO: 需要在文档中给出如何查看有哪些播放设备的方法
    parser.add_argument(
        '--mpv-audio-device',
        default='auto',
        help='（高级选项）给 mpv 播放器指定播放设备'
    )
    return parser


def enable_mac_hotkey(force=False):
    try:
        from .global_hotkey_mac import MacGlobalHotkeyManager
    except ImportError as e:
        logger.warning("Can't start mac hotkey listener: %s", str(e))
    else:
        mac_global_hotkey_mgr = MacGlobalHotkeyManager()
        if os.environ.get('TMUX') is not None and force is not True:
            logger.warning('经测试，macOS 的全局快捷键不能在 tmux 中使用!'
                           '你可以在启动时加入 `--force-mac-hotkey` 选项来强制开启。')
        else:
            mac_global_hotkey_mgr.start()


def main():
    parser = setup_argparse()
    args = parser.parse_args()

    run_as_daemon = args.daemon
    run_once = False
    is_daemon_started = check_daemon_started()

    # TODO: 将 CliMode 改成 DaemonMode

    if args.cmd is not None:  # 当命令行工具来使用
        run_once, run_as_daemon = True, False
        # 服务端不启动也能执行的命令
        cli_cmds = ('show', 'play', 'search')
        # 如果服务端已经启动，则将命令发送给服务端处理
        if is_daemon_started:
            return climain()
        if args.cmd not in cli_cmds:
            print_error('Fuo daemon not started.')
            return

    if args.version:
        print('feeluown {}, fuocore {}'.format(feeluown_version, fuocore_version))
        return

    if run_as_daemon and is_daemon_started:
        print_error('Fuo daemon is already started.')
        sys.exit(1)

    if not (run_as_daemon or run_once):
        return

    # 让程序能正确的找到图标等资源
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))
    sys.excepthook = excepthook

    ensure_dirs()
    config = create_config()
    load_rcfile(config)
    map_args_to_config(args, config)
    logger_config(config.DEBUG, to_file=args.log_to_file)

    if config.MODE & App.GuiMode:
        try:
            import PyQt5  # noqa
        except ImportError:
            logger.warning('PyQt5 is not installed，can only use CLI mode.')
            config.MODE = App.CliMode

    if config.MODE & App.GuiMode:
        from PyQt5.QtWidgets import QApplication
        from quamash import QEventLoop

        q_app = QApplication(sys.argv)
        q_app.setQuitOnLastWindowClosed(True)
        q_app.setApplicationName('FeelUOwn')

        app_event_loop = QEventLoop(q_app)
        asyncio.set_event_loop(app_event_loop)

    event_loop = asyncio.get_event_loop()
    Signal.setup_aio_support(loop=event_loop)
    app = create_app(config)
    bind_signals(app)
    if sys.platform.lower() == 'darwin':
        enable_mac_hotkey(force=config.FORCE_MAC_HOTKEY)
    try:
        event_loop.run_forever()
    except KeyboardInterrupt:
        # NOTE: gracefully shutdown?
        pass
    finally:
        event_loop.stop()
        app.shutdown()
        event_loop.close()


if __name__ == '__main__':
    main()
