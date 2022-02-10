import pytest
from feeluown.server.excs import FuoSyntaxError
from feeluown.server.dslv2 import tokenize, Parser, unparse, parse


def test_tokenize():
    tokens = tokenize('search zjl -s=xx')
    assert tokens == ['search', 'zjl', '-s=xx']

    tokens = tokenize('exec "app.exit()"')
    assert tokens == ['exec', 'app.exit()']


def test_tokenize_unquoted_source():
    with pytest.raises(FuoSyntaxError):
        tokenize("search zjl -s='xx")


def test_tokenize_source_with_heredoc():
    with pytest.raises(FuoSyntaxError):
        tokenize("search zjl -s='xx\n'\nx")


def test_parse():
    req = Parser('search zjl -s=xx').parse()
    assert req.cmd == 'search'
    assert req.cmd_args == ['zjl']
    assert req.cmd_options['source'] == ['xx']

    req = Parser('set --format=json').parse()
    assert req.cmd == 'set'
    assert req.options['format'] == 'json'


def test_parse_with_heredoc():
    req = Parser('''exec <<EOF''').parse()
    assert req.cmd == 'exec'
    assert req.has_heredoc is True
    assert req.heredoc_word == 'EOF'


def test_parse_with_invalid_iohere_token():
    with pytest.raises(FuoSyntaxError):
        Parser("exec <test.py").parse()

    with pytest.raises(FuoSyntaxError):
        Parser("exec <<").parse()

    with pytest.raises(FuoSyntaxError):
        Parser("exec <<<").parse()

    with pytest.raises(FuoSyntaxError):
        Parser("exec <<<EOF").parse()

    with pytest.raises(FuoSyntaxError):
        Parser("search EOF >").parse()


def test_unparse():
    req = Parser('search zjl -s=xx --format=json').parse()
    text = unparse(req)
    assert text == 'search zjl --source=xx --format=json'

    req = parse("search 'zjl()'")
    text = unparse(req)
    assert text == "search 'zjl()'"
