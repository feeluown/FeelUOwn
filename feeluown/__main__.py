#! /usr/bin/env python3

import argparse
import asyncio
import logging
import os
import textwrap
import traceback
import sys

from fuocore.dispatch import Signal
from fuocore.utils import is_port_used

from feeluown.app import App, create_app
from feeluown.cli import climain, oncemain, print_error, setup_cli_argparse
from feeluown import logger_config, __version__ as feeluown_version
from feeluown.consts import (
    HOME_DIR, USER_PLUGINS_DIR, DATA_DIR,
    CACHE_DIR, USER_THEMES_DIR, SONG_DIR, COLLECTIONS_DIR
)
from feeluown.rcfile import load_rcfile

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
    config.deffield('MODE', default=0x0000, desc='CLI or GUI 模式')
    config.deffield('THEME', default='auto', desc='auto/light/dark')
    config.deffield('MPV_AUDIO_DEVICE', default='auto', desc='MPV 播放设备')
    config.deffield('COLLECTIONS_DIR',  desc='本地收藏所在目录')
    config.deffield('FORCE_MAC_HOTKEY', desc='强制开启 macOS 全局快捷键功能',
                    warn='Will be remove in version 3.0')
    config.deffield('LOG_TO_FILE', desc='将日志输出到文件中')
    config.deffield('AUDIO_SELECT_POLICY', default='hq<>')
    config.deffield('VIDEO_SELECT_POLICY', default='hd<>')
    return config


def setup_argparse():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent('''\
        FeelUOwn - modern music player (daemon).

        Example:
            - fuo                        # start fuo server
            - fuo status                 # lookup server status
            - fuo play 晴天-周杰伦       # search and play
        '''),
        formatter_class=argparse.RawTextHelpFormatter,
        prog='feeluown')

    setup_cli_argparse(parser)

    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s {}'.format(feeluown_version))
    parser.add_argument('-ns', '--no-server', action='store_true', default=False,
                        help='不运行 server')
    parser.add_argument('-nw', '--no-window', action='store_true', default=False,
                        help='不显示 GUI')

    # options about log
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='开启调试模式')
    parser.add_argument('-v', '--verbose', action='count',
                        help='输出详细的日志')
    parser.add_argument('--log-to-file', action='store_true', default=False,
                        help='将日志打到文件中')

    # XXX: 不知道能否加一个基于 regex 的 option？比如加一个
    # `--mpv-*` 的 option，否则每个 mpv 配置我都需要写一个 option？

    # TODO: 需要在文档中给出如何查看有哪些播放设备的方法
    parser.add_argument(
        '--mpv-audio-device', help='（高级选项）指定播放设备')
    return parser


def enable_mac_hotkey():
    try:
        from .global_hotkey_mac import MacGlobalHotkeyManager
    except ImportError as e:
        logger.warning("Can't start mac hotkey listener: %s", str(e))
    else:
        mac_global_hotkey_mgr = MacGlobalHotkeyManager()
        mac_global_hotkey_mgr.start()


def prepare_gui():
    from PyQt5.QtWidgets import QApplication
    from quamash import QEventLoop

    q_app = QApplication(sys.argv)
    q_app.setQuitOnLastWindowClosed(True)
    q_app.setApplicationName('FeelUOwn')

    app_event_loop = QEventLoop(q_app)
    asyncio.set_event_loop(app_event_loop)
    return True


def init(args, config):
    """
    1: run cli or simple cmd
    0: run loop
    -1: error
    """
    # 让程序能正确的找到图标资源
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))
    sys.excepthook = excepthook
    ensure_dirs()

    # 从 rcfile 中加载配置和代码
    load_rcfile(config)

    # 根据命令行参数来更新配置
    # 注：用户在 rcfile 文件中也可以配置这些选项的值
    # 所以我们不能这样实现 config.DEBUG = args.debug，而是像下面这样
    config.DEBUG = args.debug or config.DEBUG
    config.MPV_AUDIO_DEVICE = args.mpv_audio_device or config.MPV_AUDIO_DEVICE
    config.LOG_TO_FILE = bool(args.log_to_file or config.LOG_TO_FILE)

    if args.cmd is not None:
        # load some config before start run_cli
        run_cli(args, config)
        return 1

    if not args.no_window:
        try:
            import PyQt5  # noqa
        except ImportError:
            logger.warning('PyQt5 is not installed, can only use daemon mode.')
        else:
            config.MODE |= App.GuiMode
    if not args.no_server:
        config.MODE |= App.DaemonMode


def setup_app(args, config):
    if config.DEBUG:
        verbose = 3
    else:
        verbose = args.verbose or 0
    logger_config(verbose=verbose, to_file=config.LOG_TO_FILE)
    Signal.setup_aio_support()
    app = create_app(config)
    return app


def run_cli(args, config):
    is_daemon_started = is_port_used(23333) or is_port_used(23334)
    if is_daemon_started:
        climain(args)
        sys.exit(0)
    cli_cmds = ('show', 'play', 'search')
    # 如果服务端已经启动，则将命令发送给服务端处理
    if args.cmd not in cli_cmds:
        print_error('Fuo daemon not started.')
        sys.exit(1)
    run_once(args, config)


def run_once(args, config):
    import warnings
    warnings.filterwarnings("ignore")

    config.MODE = App.CliMode
    app = setup_app(args, config)
    oncemain(app, args)
    app.shutdown()
    sys.exit(0)


def run_forever(args, config):
    is_daemon_started = is_port_used(23333) or is_port_used(23334)
    if config.MODE & App.DaemonMode and is_daemon_started:
        print_error('Fuo daemon is already started.')
        sys.exit(1)

    if config.MODE & App.GuiMode:
        prepare_gui()
    app = setup_app(args, config)
    if sys.platform.lower() == 'darwin':
        enable_mac_hotkey()
    loop = asyncio.get_event_loop()
    try:
        if not config.MODE & App.GuiMode:
            if config.MODE & App.DaemonMode:
                # when started with daemon mode, show some message to tell user
                # that the program is running.
                print('Fuo daemon running on 0.0.0.0:23333 (tcp)')
            else:
                print('Fuo running with no daemon and no window')
        loop.run_forever()
    except KeyboardInterrupt:
        # NOTE: gracefully shutdown?
        pass
    finally:
        loop.stop()
        app.shutdown()
        loop.close()


def main():
    """
    启动步骤：

    1. 判断是否只需要运行一次客户端
       比如运行 fuo status 命令
    2.
    """
    parser = setup_argparse()
    args = parser.parse_args()
    config = create_config()
    res = init(args, config)
    if res != 1:
        run_forever(args, config)


if __name__ == '__main__':
    main()
