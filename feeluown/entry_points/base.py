import argparse
import logging
import os
import textwrap

from feeluown import logger_config, __version__ as feeluown_version
from feeluown.app import App
from feeluown.cli import setup_cli_argparse
from feeluown.config import Config
from feeluown.consts import (
    HOME_DIR, USER_PLUGINS_DIR, DATA_DIR,
    CACHE_DIR, USER_THEMES_DIR, SONG_DIR, COLLECTIONS_DIR
)

logger = logging.getLogger(__name__)


def ensure_dirs():
    for d in (HOME_DIR,
              DATA_DIR,
              USER_THEMES_DIR,
              USER_PLUGINS_DIR,
              CACHE_DIR,
              SONG_DIR,
              COLLECTIONS_DIR):
        if not os.path.exists(d):
            os.mkdir(d)


def create_config():
    config = Config()
    config.deffield('DEBUG', type_=bool, desc='是否为调试模式')
    config.deffield('VERBOSE', default=0, type_=int, desc='日志详细程度')
    config.deffield('MODE', default=0x0000, desc='CLI or GUI 模式')
    config.deffield('THEME', default='auto', desc='auto/light/dark')
    config.deffield('MPV_AUDIO_DEVICE', default='auto', desc='MPV 播放设备')
    config.deffield('COLLECTIONS_DIR',  desc='本地收藏所在目录')
    config.deffield('FORCE_MAC_HOTKEY', desc='强制开启 macOS 全局快捷键功能',
                    warn='Will be remove in version 3.0')
    config.deffield('LOG_TO_FILE', desc='将日志输出到文件中')
    config.deffield('AUDIO_SELECT_POLICY', default='hq<>')
    config.deffield('VIDEO_SELECT_POLICY', default='hd<>')
    config.deffield('ALLOW_LAN_CONNECT', type_=bool, default=False, desc='是否可以从局域网连接服务器')
    config.deffield('PROVIDERS_STANDBY', type_=list, default=None, desc='')
    config.deffield('ENABLE_TRAY', type_=bool, default=True, desc='启用系统托盘')
    config.deffield('NOTIFY_ON_TRACK_CHANGED', type_=bool, default=False,
                    desc='切换歌曲时显示桌面通知')
    config.deffield('NOTIFY_DURATION', type_=int, default=3000, desc='桌面通知保留时长(ms)')
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


def setup_config(args, config):
    config.DEBUG = args.debug or config.DEBUG
    config.VERBOSE = args.verbose or config.VERBOSE
    config.MPV_AUDIO_DEVICE = args.mpv_audio_device or config.MPV_AUDIO_DEVICE
    config.LOG_TO_FILE = bool(args.log_to_file or config.LOG_TO_FILE)

    if args.cmd is not None:
        config.MODE = App.CliMode
    else:
        if not args.no_window:
            try:
                import PyQt5  # noqa, pylint: disable=unused-import
            except ImportError:
                logger.warning('PyQt5 is not installed, fallback to daemon mode.')
            else:
                try:
                    from feeluown.utils.compat import QEventLoop  # noqa
                except ImportError:
                    logger.warning('no QEventLoop, fallback to daemon mode.')
                else:
                    config.MODE |= App.GuiMode
        if not args.no_server:
            config.MODE |= App.DaemonMode


def setup_logger(config):
    if config.DEBUG:
        verbose = 3
    else:
        verbose = config.VERBOSE
    logger_config(verbose=verbose, to_file=config.LOG_TO_FILE)
