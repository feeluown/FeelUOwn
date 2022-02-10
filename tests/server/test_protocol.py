import asyncio
from unittest import mock, TestCase

import pytest

from feeluown.server.protocol import FuoServerProtocol, read_request
from feeluown.server.dslv2 import parse


async def coro():
    return None


@pytest.mark.asyncio
async def test_read_request():
    reader = asyncio.StreamReader()

    # Read a valid request.
    reader.feed_data(b'search zjl\n')
    req = await read_request(reader, parse)
    assert req.cmd == 'search'

    # Read a new line.
    reader.feed_data(b'\n')
    req = await read_request(reader, parse)
    assert req is None

    # Read a request with heredoc.
    reader.feed_data(b'exec <<EOF\n')
    reader.feed_data(b'EOF\n')
    req = await read_request(reader, parse)
    assert req.has_heredoc is True

    # Read an invalid request.
    reader.feed_data(b'xx yy\n')
    with pytest.raises(Exception):
        await read_request(reader, parse)


# ignore RuntimeWaarnig:
# coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
@pytest.mark.filterwarnings('ignore:coroutine')
class TestFuoServerProtocol(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        self.protocol = FuoServerProtocol(handle_req=lambda: (), loop=self.loop)

    @mock.patch.object(FuoServerProtocol, 'start', return_value=coro())
    def test_connection_made(self, mock_start):
        """reader and writer should be inited, start task should be created"""
        transport = mock.Mock()
        self.protocol.connection_made(transport)
        self.assertIsNotNone(self.protocol._reader)
        self.assertIsNotNone(self.protocol._writer)

    @mock.patch.object(asyncio.StreamWriter, 'drain')
    def test_start_write_drain(self, mock_drain):
        """drain should be called after start coro runs"""
        async def func():
            return None
        mock_drain.side_effect = func
        transport = mock.Mock()
        self.protocol.connection_made(transport)
        self.protocol._connection_lost = True
        self.loop.run_until_complete(self.protocol.start())
        self.assertTrue(mock_drain.called)

    @mock.patch.object(asyncio.StreamReader, 'readline')
    def test_start_readline(self, mock_readline):
        """readline should be called after start coro runs"""
        writer = mock.Mock()
        writer.drain = coro
        mock_readline.side_effect = ConnectionResetError
        self.protocol._reader = asyncio.StreamReader(loop=self.loop)
        self.protocol._writer = writer
        self.loop.run_until_complete(self.protocol.start())
        self.assertTrue(mock_readline.called)

    @mock.patch.object(asyncio.StreamReader, 'feed_eof')
    @mock.patch.object(FuoServerProtocol, 'start', return_value=coro())
    def test_connection_lost(self, mock_start, mock_feed_eof):
        """connection_lost should feed_eof"""
        transport = mock.Mock()
        self.protocol.connection_made(transport)
        self.protocol.connection_lost(None)
        self.assertTrue(mock_feed_eof.called)

    @mock.patch.object(FuoServerProtocol, 'start', return_value=coro())
    def test_eof_received(self, mock_start):
        """eof_received should return False or None"""
        transport = mock.Mock()
        self.protocol.connection_made(transport)
        self.assertFalse(self.protocol.eof_received())

    def tearDown(self):
        self.loop.close()
        self.loop = None
        self.protocol = None
