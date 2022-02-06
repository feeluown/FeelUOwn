from feeluown.server import dslv1
from feeluown.server import Request


def test_request():
    req = Request(cmd='play', cmd_args=['fuo://x'])
    assert 'play fuo://x' in dslv1.unparse(req)
