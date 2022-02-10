import argparse

from feeluown.argparser import add_common_cmds, add_server_cmds


def test_argparse():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest='cmd',
    )
    add_common_cmds(subparsers)
    add_server_cmds(subparsers)

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
    assert args.type == [argv[-1]]
    # Test parse invalid args.
    argv = ['search', 'zjl', '-t', 'xx']
    args, remain = parser.parse_known_args(argv)
    assert remain == argv[-2:]
