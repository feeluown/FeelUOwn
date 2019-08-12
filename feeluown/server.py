import asyncio
import logging

from fuocore.protocol import FuoServerProtocol, Response
from fuocore.cmds import exec_cmd, Cmd

logger = logging.getLogger(__name__)


class FuoServer:
    def __init__(self, app):
        self._app = app
        self._loop = None

    async def run(self, host='0.0.0.0', port=23333):
        loop = asyncio.get_event_loop()
        self._loop = loop
        await loop.create_server(self.protocol_factory, host, port)
        logger.info('Fuo daemon run at {}:{}'.format(host, port))

    def protocol_factory(self):
        return FuoServerProtocol(handle_req=self.handle_req,
                                 loop=self._loop)

    def handle_req(self, req, session=None):
        cmd = Cmd(req.cmd, *req.cmd_args, options=req.cmd_options)
        success, msg = exec_cmd(
            cmd,
            library=self._app.library,
            player=self._app.player,
            playlist=self._app.playlist,
            live_lyric=self._app.live_lyric)
        code = 'ok' if success else 'oops'
        return Response(code=code, msg=msg, req=req)
