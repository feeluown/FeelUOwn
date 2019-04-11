import asyncio
import logging

from fuocore.protocol import FuoServerProtocol, Response
from fuocore.cmds import exec_cmd, Cmd, CmdException

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
        await loop.create_server(self.protocol_factory, host, port)
        logger.info('Fuo daemon run at {}:{}'.format(host, port))

    def protocol_factory(self):
        return FuoServerProtocol(req_handler=self.handle_req,
                                 loop=self._loop)

    def handle_req(self, req, session=None):
        cmd = Cmd(req.cmd, *req.cmd_args)
        success, msg = exec_cmd(
            cmd,
            library=self._library,
            player=self._player,
            playlist=self._playlist,
            live_lyric=self._live_lyric)
        code = 'ok' if success else 'oops'
        return Response(code=code, msg=msg, req=req)
