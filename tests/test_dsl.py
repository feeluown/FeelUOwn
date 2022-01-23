import argparse

import pytest

from feeluown.dsl import add_cmd_parser, tokenize


@pytest.fixture
def parser():
    return argparse.ArgumentParser(exit_on_error=False)


def test_rpc_parsers(parser: argparse.ArgumentParser):
    add_cmd_parser(parser)

    # Test play parser.
    argv = ['play', 'fuo://xxx']
    args = parser.parse_args(argv)
    assert args.cmd == argv[0]

    # Test format parser.
    argv = ['search', 'zjl', '--format', 'json']
    args = parser.parse_args(argv)
    assert args.format == argv[3]
    argv = ['search', 'zjl', '--json']
    args = parser.parse_args(argv)
    assert args.json is True

    # Test search parser.
    argv = ['search', 'zjl', '--source', 'xx', '--s', 'yy', '--type', 'song']
    args = parser.parse_args(argv)
    assert args.keyword == argv[1]
    assert 'xx' in args.source and 'yy' in args.source
    assert args.type == argv[-1]
    # Test parse invalid args.
    argv = ['search', 'zjl', '-t', 'xx']
    args, remain = parser.parse_known_args(argv)
    assert remain == argv[-2:]


def test_tokenize():
    tokens = tokenize('search zjl -s=xx')
    assert tokens == ['search', 'zjl', '-s=xx']
