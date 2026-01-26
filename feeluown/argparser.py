import argparse
import textwrap
from functools import partial

from feeluown.i18n import t


def create_fmt_parser():
    fmt_parser = argparse.ArgumentParser(add_help=False)
    fmt_parser.add_argument(
        "--format",
        help="change command output format (default: plain)",
        choices=["plain", "json"],
    )
    fmt_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="change command output format to json",
    )
    fmt_parser.add_argument(
        "--plain",
        action="store_true",
        default=False,
        help="change command output format to plan",
    )
    return fmt_parser


def add_common_cmds(subparsers: argparse._SubParsersAction):
    fmt_parser = create_fmt_parser()
    parents = [fmt_parser]

    add_parser = partial(subparsers.add_parser, parents=parents)

    # Create parsers.
    #
    play_parser = add_parser(
        "play",
        description=textwrap.dedent("""\
        Example:
            - fuo play fuo://netease/songs/3027393
            - fuo play "in the end"
            - fuo play 稻香-周杰伦
        """),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    show_parser = add_parser(
        "show",
        help="显示资源详细信息",
    )
    search_parser = add_parser(
        "search",
        description=textwrap.dedent("""\
        Example:
            - fuo search hero
            - fuo search 李宗盛 source=xiami,type=artist
            - fuo search 李宗盛 [source=xiami,type=artist]
            - fuo search lizongsheng "source='xiami,qq',type=artist"
            - fuo search 李宗盛 "[source='xiami,qq',type=artist]"
        """),
        formatter_class=argparse.RawTextHelpFormatter,
        parents=parents,
    )
    remove_parser = add_parser("remove", help=t("command-track-remove"))
    add_parser_ = add_parser("add", help=t("command-track-add"))
    exec_parser = add_parser("exec")
    jsonrpc_parser = add_parser("jsonrpc")
    add_parser("pause", help=t("command-playback-pause"))
    add_parser("resume", help=t("command-playback-resume"))
    add_parser("toggle", help="")
    add_parser("stop")
    add_parser("next")
    add_parser("previous")
    add_parser("list")
    add_parser("clear")
    add_parser("status")

    # Initialize parsers.
    #
    play_parser.add_argument("uri")
    show_parser.add_argument("uri")
    remove_parser.add_argument("uri")
    add_parser_.add_argument("uri", nargs="?")
    search_parser.add_argument("keyword", help=t("command-search"))
    search_parser.add_argument("-s", "--source", action="append")
    search_parser.add_argument(
        "--type",
        action="append",
        type=str,
        choices=["song", "album", "artist", "video", "playlist"],
    )
    exec_parser.add_argument("code", nargs="?", help=t("command-exec-code"))
    jsonrpc_parser.add_argument("body", nargs="?", help=t("command-jsonrpc-body"))


def add_cli_cmds(subparsers: argparse._SubParsersAction):
    # Generate desktop file/icon.
    subparsers.add_parser("genicon", description="generate desktop icon")


def add_server_cmds(subparsers: argparse._SubParsersAction, include_pubsub=True):
    fmt_parser = create_fmt_parser()
    subparsers.add_parser(
        "quit",
        parents=[fmt_parser],
    )
    help_parser = subparsers.add_parser(
        "help",
        parents=[fmt_parser],
    )
    help_parser.add_argument("cmdname")
    # The default value of these values should be None.
    # See set handler for more details.
    set_parser = subparsers.add_parser(
        "set",
        help="设置会话参数",
        parents=[fmt_parser],
    )
    set_parser.add_argument(
        "--rpc-version",
        type=str,
        choices=["1.0", "2.0"],
    )
    set_parser.add_argument(
        "--pubsub-version",
        type=str,
        choices=["1.0", "2.0"],
    )

    if include_pubsub is True:
        sub_parser = subparsers.add_parser(
            "sub",
            help="订阅主题消息",
            parents=[fmt_parser],
        )
        sub_parser.add_argument(
            "topics",
            nargs="?",
            help="主题名字",
        )


def _create_cli_parser() -> argparse.ArgumentParser:
    # pylint: disable=import-outside-toplevel
    from feeluown import __version__ as feeluown_version

    parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """\
        FeelUOwn - modern music player (daemon).

        Example:
            - fuo                        # start fuo server
            - fuo status                 # lookup server status
            - fuo play 晴天-周杰伦       # search and play
        """
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        prog="feeluown",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s {}".format(feeluown_version),
    )
    parser.add_argument(
        "-ns",
        "--no-server",
        action="store_true",
        default=False,
        help=t("cli-no-server"),
    )
    parser.add_argument(
        "-nw",
        "--no-window",
        action="store_true",
        default=False,
        help=t("cli-no-window"),
    )

    # options about log
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help=t("cli-debug-mode"),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help=t("cli-verbose"),
    )
    parser.add_argument(
        "--log-to-file",
        action="store_true",
        default=False,
        help=t("cli-log-to-file"),
    )

    # XXX: Not sure if it's possible to add a regex-based option?
    # For example, a `--mpv-*` option, otherwise I’d need to write
    # an option for each mpv configuration?

    # TODO: Need to include in the documentation
    # how to view the available playback devices.
    parser.add_argument(
        "--mpv-audio-device",
        help=t("cli-mpv-audio-device"),
    )
    return parser


def create_cli_parser() -> argparse.ArgumentParser:
    parser = _create_cli_parser()
    subparsers = parser.add_subparsers(
        dest="cmd",
    )

    add_common_cmds(subparsers)
    add_cli_cmds(subparsers)
    return parser
