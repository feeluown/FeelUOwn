import pytest
from feeluown.server.excs import FuoSyntaxError
from feeluown.server.dslv2 import tokenize


def test_tokenize():
    tokens = tokenize('search zjl -s=xx')
    assert tokens == ['search', 'zjl', '-s=xx']


def test_tokenize_unquoted_source():
    with pytest.raises(FuoSyntaxError):
        tokenize("search zjl -s='xx")


def test_tokenize_source_with_heredoc():
    with pytest.raises(FuoSyntaxError):
        print(tokenize("search zjl -s='xx\n'\nx"))
