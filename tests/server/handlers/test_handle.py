import json

import pytest

from feeluown.server import handle_request, Request
from feeluown.server.handlers.search import SearchHandler


@pytest.fixture
def req():
    return Request(
        cmd='search',
        cmd_args=['zjl'],
        cmd_options={'type': ['song']},
        options={'format': 'json'}
    )


@pytest.mark.asyncio
async def test_handle_request(req, app_mock, mocker):
    result = []
    mocker.patch.object(SearchHandler, 'search', return_value=result)
    resp = await handle_request(req, app_mock, mocker.Mock())
    assert resp.code == 'OK'
    assert json.loads(resp.text) == result
