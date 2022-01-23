from feeluown.server.rpc.data_structure import Request


def test_request():
    req = Request(cmd='play', cmd_args=['fuo://x'])
    assert 'play fuo://x' in req.raw
