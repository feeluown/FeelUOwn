import asyncio
from unittest import mock, TestCase

from fuocore.protocol import FuoServerProtocol


async def coro():
    return None


class TestFuoServerProtocol(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        self.protocol = FuoServerProtocol(self.loop)

    @mock.patch.object(FuoServerProtocol, 'start')
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
    @mock.patch.object(FuoServerProtocol, 'start')
    def test_connection_lost(self, mock_start, mock_feed_eof):
        """connection_lost should feed_eof"""
        transport = mock.Mock()
        self.protocol.connection_made(transport)
        self.protocol.connection_lost(None)
        self.assertTrue(mock_feed_eof.called)

    @mock.patch.object(FuoServerProtocol, 'start')
    def test_eof_received(self, mock_start):
        """eof_received should return False or None"""
        transport = mock.Mock()
        self.protocol.connection_made(transport)
        self.assertFalse(self.protocol.eof_received())

    def tearDown(self):
        self.loop.close()
        self.loop = None
        self.protocol = None
