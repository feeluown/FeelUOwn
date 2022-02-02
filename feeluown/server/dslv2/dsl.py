"""
The DSL is used for RPC and resource definition. The syntax of the DSL is same
as UNIX shell.

>>> import argparse
>>> from feeluown.argparse import add_cmd_parser
>>> parser = argparse.ArgumentParser()
>>> add_cmd_parser(parser)
>>> tokens = tokenize("search jaychou -s=xx")
>>> args = parser.parse_args(tokens)
>>> args.cmd, args.source, args.keyword
('search', ['xx'], 'jaychou')

"""

import shlex


def tokenize(source):
    s = shlex.shlex(source, punctuation_chars=True, posix=True)
    s.whitespace_split = True
    return list(s)
