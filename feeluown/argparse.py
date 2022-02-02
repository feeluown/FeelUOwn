import argparse
import textwrap


def add_format_parser(parser: argparse.ArgumentParser):
    fmt_parser = argparse.ArgumentParser(add_help=False)
    fmt_parser.add_argument(
        '--format',
        help="change command output format (default: plain)",
        choices=['plain', 'json'],
    )
    fmt_parser.add_argument(
        '--json',
        action='store_true',
        default=False,
        help="change command output format to json",
    )
    fmt_parser.add_argument(
        '--plain',
        action='store_true',
        default=False,
        help="change command output format to plan"
    )
    return fmt_parser


def add_rpc_parsers(subparsers: argparse._SubParsersAction,
                    fmt_parser: argparse.ArgumentParser):
    parents = [fmt_parser]

    # Create parsers.
    #
    play_parser = subparsers.add_parser(
        'play',
        description=textwrap.dedent('''\
        Example:
            - fuo play fuo://netease/songs/3027393
            - fuo play "in the end"
            - fuo play 稻香-周杰伦
        '''),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    show_parser = subparsers.add_parser(
        'show',
        help='显示资源详细信息',
        parents=parents,
    )
    search_parser = subparsers.add_parser(
        'search',
        description=textwrap.dedent('''\
        Example:
            - fuo search hero
            - fuo search 李宗盛 source=xiami,type=artist
            - fuo search 李宗盛 [source=xiami,type=artist]
            - fuo search lizongsheng "source='xiami,qq',type=artist"
            - fuo search 李宗盛 "[source='xiami,qq',type=artist]"
        '''),
        formatter_class=argparse.RawTextHelpFormatter,
        parents=parents,
    )
    remove_parser = subparsers.add_parser('remove', help='从播放列表移除歌曲')
    add_parser = subparsers.add_parser('add', help='添加歌曲到播放列表')
    exec_parser = subparsers.add_parser('exec')
    subparsers.add_parser('pause', help='暂停播放')
    subparsers.add_parser('resume', help='回复播放')
    subparsers.add_parser('toggle', help='')
    subparsers.add_parser('stop')
    subparsers.add_parser('next')
    subparsers.add_parser('previous')
    subparsers.add_parser('list', parents=parents)
    subparsers.add_parser('clear')
    subparsers.add_parser('status', parents=parents)

    # Initialize parsers.
    #
    play_parser.add_argument('uri')
    show_parser.add_argument('uri')
    remove_parser.add_argument('uri')
    add_parser.add_argument('uri', nargs='?')
    search_parser.add_argument('keyword', help='搜索关键字')
    search_parser.add_argument('-s', '--source', action='append')
    search_parser.add_argument(
        '--type',
        type=str,
        choices=['song', 'album', 'artist', 'video', 'playlist']
    )
    exec_parser.add_argument('code', nargs='?', help='Python 代码')


def add_cmd_parser(parser: argparse.ArgumentParser):
    subparsers = parser.add_subparsers(
        dest='cmd',
    )

    # Initialize global options.
    fmt_parser = add_format_parser(parser)

    # Generate desktop file/icon.
    subparsers.add_parser(
        'genicon',
        description='generate desktop icon'
    )
    add_rpc_parsers(subparsers, fmt_parser)
