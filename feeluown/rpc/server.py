import asyncio
import logging

from feeluown.serializers import serialize
from .cmds import exec_cmd, Cmd
from .server_protocol import FuoServerProtocol, Response


logger = logging.getLogger(__name__)
_REGISTERED = False


def register_feeluown_serializers():
    from feeluown.serializers.app import (  # noqa
        AppPythonSerializer,
        AppPlainSerializer
    )
    global _REGISTERED
    _REGISTERED = True


def handle_request(req, app, ctx=None):
    """
    :type req: feeluown.rpc.Request
    """
    if not _REGISTERED:
        register_feeluown_serializers()

    cmd = Cmd(req.cmd, *req.cmd_args, options=req.cmd_options)
    ok, body = exec_cmd(cmd, app=app)
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
        try:
            await loop.create_server(self.protocol_factory, host, port)
        except OSError as e:
            raise SystemExit(str(e)) from None
        logger.info('Fuo daemon run at {}:{}'.format(host, port))

    def protocol_factory(self):
        return FuoServerProtocol(handle_req=self.handle_req,
                                 loop=self._loop)

    def handle_req(self, req, session=None):
        return handle_request(req, self._app, ctx=session)
