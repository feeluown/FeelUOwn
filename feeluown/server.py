import asyncio
import logging

from fuocore.protocol import FuoServerProtocol

logger = logging.getLogger(__name__)


class FuoServer:
    def __init__(self, *, loop, library, player, playlist, live_lyric):
        self._loop = loop
        self._library = library
        self._player = player
        self._playlist = playlist
        self._live_lyric = live_lyric

    async def run(self, host='0.0.0.0', port=23333):
        loop = asyncio.get_event_loop()
        server = await loop.create_server(self.protocol_factory, host, port)
        async with server:
            await server.serve_forever()
        logger.info('Fuo daemon run at {}:{}'.format(host, port))

    def protocol_factory(self):
        return FuoServerProtocol(loop=self._loop)
