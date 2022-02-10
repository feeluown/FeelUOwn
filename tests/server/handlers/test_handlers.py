from unittest.mock import call

import pytest

from feeluown.server.handlers.sub import SubHandler
from feeluown.server.handlers.help import HelpHandler


@pytest.fixture
def session_mock(mocker):
    return mocker.Mock()


def test_handle_sub(app_mock, session_mock):
    handler = SubHandler(app_mock, session_mock)
    mock_link = app_mock.pubsub_gateway.link
    app_mock.pubsub_gateway.topics = [
        'player.seeked',
        'player.media_changed'
    ]
    handler.handle_sub('player.*')

    mock_link.assert_has_calls([
        call(topic, session_mock)
        for topic in app_mock.pubsub_gateway.topics
    ])


def test_handle_help(app_mock, session_mock):
    handler = HelpHandler(app_mock, session_mock)
    # No error should occur.
    handler.handle_help('set')
    handler.handle_help('sub')

    result = handler.handle_help('status')
    assert 'usage' in result
