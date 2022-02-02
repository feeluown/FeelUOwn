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
            raise FuoSyntaxError("Source must be only one line")
        return tokens


def parse(source):
    pass


def request_as_raw(req):
    # add_cmd_parser(parser)
    # argv = ['search', 'zjl', '--source', 'xx', '--s', 'yy', '--type', 'song']
    # args = parser.parse_args(argv)
    # for action in parser._actions:
    #     if action.dest == 'cmd':
    #         m = action._name_parser_map
    #         search = m['search']
    #         for action in search._positionals._group_actions:
    #             print
    pass
