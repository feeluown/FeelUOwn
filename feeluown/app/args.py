"""
feeluown.app.args
~~~~~~~~~~~~~~~~~

App command line args.
"""

import argparse

from feeluown import __version__ as feeluown_version


def init_args_parser(parser: argparse.ArgumentParser):
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
