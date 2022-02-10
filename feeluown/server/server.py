import asyncio
import logging

from feeluown.server import handle_request
from feeluown.server.session import SessionLike
from .protocol import FuoServerProtocol, ProtocolType, PubsubProtocol


logger = logging.getLogger(__name__)


class FuoServer:
    def __init__(self, app, protocol_type):
        self._app = app
        self.protocol_type = protocol_type
        self._loop = None

    async def run(self, host, port):
        loop = asyncio.get_event_loop()
        self._loop = loop

        try:
            await loop.create_server(self.protocol_factory, host, port)
        except OSError as e:
            raise SystemExit(str(e)) from None

        name = 'unknown'
        if self.protocol_type is ProtocolType.rpc:
            name = 'PRC'
        elif self.protocol_type is ProtocolType.pubsub:
            name = 'Pub/Sub'
        logger.info('%s server run at %s:%d', name, host, port)

    def protocol_factory(self):
        if self.protocol_type is ProtocolType.rpc:
            protocol_cls = FuoServerProtocol
        else:
            protocol_cls = PubsubProtocol
        return protocol_cls(handle_req=self.handle_req,
                            loop=self._loop,)

    async def handle_req(self, req, session: SessionLike):
        return await handle_request(req, self._app, session)
