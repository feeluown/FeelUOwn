"""
The DSL is used for RPC and resource definition. The syntax of the DSL is same
as UNIX shell.

>>> req = parse("search jaychou -s=xx")
>>> req.cmd
'search'
>>> req.cmd_args
['jaychou']
"""

import argparse
import shlex
import itertools
from typing import Optional

from feeluown.argparser import (
    create_fmt_parser,
    add_common_cmds,
    add_server_cmds,
)
from feeluown.server.data_structure import Request
from feeluown.server.excs import FuoSyntaxError


def tokenize(source):
    s = shlex.shlex(source, punctuation_chars=True, posix=True)
    s.whitespace_split = True
    try:
        tokens = list(s)
    except ValueError as e:
        raise FuoSyntaxError(str(e)) from None
    else:
        if s.lineno >= 2:
            raise FuoSyntaxError("source must be only one line")
        return tokens


class ArgumentParserNoExitAndPrint(argparse.ArgumentParser):
    """
    This customized argument parser class is design to handle two scenario
    1. When there is an error, the parser should not exit. So the error method is
       overrided.
    2. When `help` action is executed, the parser should not exit and it should
       not print help message to stdout/stderr either. So the `_print_message` and
       `exit` method are overrided.
    """
    def _print_message(self, message, file=None):  # noqa
        pass

    def exit(self, status=0, message=None):  # noqa
        pass

    def error(self, message):
        raise FuoSyntaxError(message)


def create_dsl_parser():
    # pylint: disable=protected-access
    parser = ArgumentParserNoExitAndPrint(add_help=False)
    subparsers = parser.add_subparsers(
        dest='cmd',
    )
    add_common_cmds(subparsers)
    add_server_cmds(subparsers)
    return parser


class Parser:
    def __init__(self, source):
        self._source = source

    def parse(self) -> Request:
        """Parse the source to a Request object.

        argparse have little public methods, so some protected methods are used.
        """
        # pylint: disable=too-many-locals,protected-access,too-many-branches
        parser: ArgumentParserNoExitAndPrint = create_dsl_parser()
        tokens = tokenize(self._source)

        # Handle io_here token.
        has_heredoc, heredoc_word = False, None
        for i, token in enumerate(tokens.copy()):
            if token == '<<':  # Heredoc document.
                has_heredoc = True
                try:
                    heredoc_word = tokens.pop(i+1)
                except IndexError:
                    raise FuoSyntaxError('no heredoc word') from None
                else:
                    tokens.pop(i)  # Pop token '<<' from tokens.
            elif token in ('<', '<<<'):
                raise FuoSyntaxError('unknown token')

        # Parse the tokens.
        args, remain = parser.parse_known_args(tokens)
        if remain:
            raise FuoSyntaxError(f'unknown tokens {tokens}')

        # Get cmdname from the parse result.
        cmdname = getattr(args, 'cmd')
        subparser = get_subparser(parser, cmdname)
        assert subparser is not None, f'parser for cmd:{cmdname} not found'

        # Get cmd args from the parse result.
        cmd_args = []
        for action in subparser._positionals._group_actions:
            cmd_args.append(getattr(args, action.dest))

        # Get req options from the parse result.
        req_options = {}
        option_names_req = []
        for parser_ in [create_fmt_parser()]:
            for action in parser_._actions:
                name = action.dest
                option_names_req.append(name)
                value = getattr(args, name)
                req_options[name] = value

        # Get cmd options from the parse result.
        cmd_options = {}
        for action in subparser._optionals._group_actions:
            option_name = action.dest
            if option_name == 'help':  # Ignore help action.
                continue
            if option_name not in option_names_req:
                cmd_options[option_name] = getattr(args, option_name)

        return Request(cmdname,
                       cmd_args,
                       cmd_options,
                       req_options,
                       has_heredoc=has_heredoc, heredoc_word=heredoc_word)


def get_subparser(parser, cmdname) -> Optional[argparse.ArgumentParser]:
    # pylint: disable=protected-access
    # Get cmdname from the parse result.
    root_dest = 'cmd'
    subparser = None
    for action in parser._actions:
        if action.dest == root_dest:
            subparser = action._name_parser_map[cmdname]  # type: ignore
            break
    return subparser


def parse(source):
    return Parser(source).parse()


def unparse(request: Request):
    """Generate source code for the request object"""
    # pylint: disable=protected-access,too-many-branches
    parser = create_dsl_parser()
    subparser = get_subparser(parser, request.cmd)
    if subparser is None:
        raise ValueError(f'{request.cmd}: no such cmd')

    cmdline = [request.cmd]

    # Unparse cmd args.
    if request.has_heredoc:
        cmdline.append(f'<<{request.heredoc_word}')
    else:
        cmdline.extend([shlex.quote(each) for each in request.cmd_args])

    # Unparse cmd options.
    for key, value in itertools.chain(
            request.cmd_options.items(), request.options.items()):
        for action in subparser._actions:
            if action.dest == key:
                # The option has a default value.
                if value is None:
                    break

                if isinstance(action, argparse._StoreTrueAction):
                    if value is True:
                        cmdline.append(f'--{key}')
                elif isinstance(action, argparse._AppendAction):
                    for each in value or []:
                        cmdline.append(f'--{key}={shlex.quote(str(each))}')
                else:
                    cmdline.append(f'--{key}={shlex.quote(str(value))}')
                break
        else:
            raise ValueError(f'{key}: no such option')

    cmdtext = ' '.join(cmdline)
    if request.has_heredoc:
        cmdtext += '\n'
        cmdtext += request.cmd_args[0]
        cmdtext += '\n'
        cmdtext += request.heredoc_word
    return cmdtext
