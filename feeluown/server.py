import asyncio
import logging

from fuocore.cmds import exec_cmd, Cmd
from fuocore.protocol import FuoServerProtocol, Response
from fuocore.serializers import serialize

logger = logging.getLogger(__name__)


def handle_request(req, app, ctx=None):
    """
    :type req: fuocore.protocol.Request
    """
    cmd = Cmd(req.cmd, *req.cmd_args, options=req.cmd_options)
    ok, body = exec_cmd(
        cmd,
        library=app.library,
        player=app.player,
        playlist=app.playlist,
        live_lyric=app.live_lyric)
    format = req.options.get('format', 'plain')
    msg = serialize(format, body, brief=False)
    return Response(ok=ok, text=msg, req=req)


class FuoServer:
    def __init__(self, app):
        self._app = app
        self._loop = None

    async def run(self, host, port=23333):
        loop = asyncio.get_event_loop()
        self._loop = loop
        await loop.create_server(self.protocol_factory, host, port)
        logger.info('Fuo daemon run at {}:{}'.format(host, port))

    def protocol_factory(self):
        return FuoServerProtocol(handle_req=self.handle_req,
                                 loop=self._loop)

    def handle_req(self, req, session=None):
        return handle_request(req, self._app, ctx=session)
