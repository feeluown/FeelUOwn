"""
The DSL is used for RPC and resource definition. The syntax of the DSL is same
as UNIX shell.

>>> import argparse
>>> from feeluown.argparse import create_dsl_parser
>>> tokens = tokenize("search jaychou -s=xx")
>>> args = create_dsl_parser().parse_args(tokens)
>>> args.cmd, args.source, args.keyword
('search', ['xx'], 'jaychou')

"""

import shlex
from feeluown.argparse import create_dsl_parser, create_fmt_parser

from feeluown.server.data_structure import Request
from feeluown.server.excs import FuoSyntaxError


def tokenize(source):
    s = shlex.shlex(source, punctuation_chars=True, posix=True)
    s.whitespace_split = True
    try:
        tokens = list(s)
    except ValueError as e:
        raise FuoSyntaxError(str(e))
    else:
        if s.lineno >= 2:
            raise FuoSyntaxError("source must be only one line")
        return tokens


class Parser:
    def __init__(self, source):
        self._source = source

    def parse(self) -> Request:
        """Parse the source to a Request object.

        argparse have little public methods, so some protected methods are used.
        """
        parser = create_dsl_parser()
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
            raise FuoSyntaxError('unknown tokens')

        # Get cmdname from the parse result.
        root_dest = 'cmd'
        cmdname = getattr(args, root_dest)
        subparser = None
        for action in parser._actions:
            if action.dest == root_dest:
                subparser = action._name_parser_map[cmdname]
                break
        assert subparser is not None, f'parser for cmd:{cmdname} not found'

        # Get cmd args from the parse result.
        cmd_args = []
        for action in subparser._positionals._group_actions:
            cmd_args.append(getattr(args, action.dest))

        # Get req options from the parse result.
        req_options = {}
        option_names_req = []
        req_options_parsers = [create_fmt_parser(), ]
        for parser in req_options_parsers:
            for action in parser._actions:
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
