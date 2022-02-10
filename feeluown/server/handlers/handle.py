import logging
from typing import Optional

from feeluown.server.data_structure import Request, Response
from feeluown.server.session import SessionLike
from feeluown.serializers import serialize
from .base import cmd_handler_mapping, AbstractHandler
from .cmd import Cmd
from .excs import HandlerException

logger = logging.getLogger(__name__)


async def handle_request(
        req: Request,
        app,
        session: Optional[SessionLike] = None
) -> Response:
    """
    :type req: feeluown.server.rpc.Request
    """
    cmd = Cmd(req.cmd, *req.cmd_args, options=req.cmd_options)

    ok, body = False, ''
    handler_cls = cmd_handler_mapping.get(cmd.action)
    if handler_cls is None:
        ok, body = False, f"handler for cmd:{req.cmd} not found"
    else:
        try:
            handler: AbstractHandler = handler_cls(app=app, session=session)
            if handler.support_aio_handle is True:
                rv = await handler.a_handle(cmd)
            else:
                # FIXME: handlers do blocking io should implement a_handle method.
                rv = handler.handle(cmd)
        except HandlerException as e:
            ok, body = False, str(e)
        except Exception:  # pylint: disable=broad-except
            logger.exception(f'handle cmd({cmd}) error')
            ok, body = False, 'internal server error'
        else:
            rv = rv if rv is not None else ''
            ok, body = True, rv
    fmt = req.options.get('format', None)
    fmt = fmt or 'plain'
    msg = serialize(fmt, body, brief=False)
    return Response(ok=ok, text=msg, req=req)


# pylint: disable=wrong-import-position, cyclic-import
from .help import HelpHandler  # noqa
from .status import StatusHandler  # noqa
from .playlist import PlaylistHandler  # noqa
from .player import PlayerHandler  # noqa
from .search import SearchHandler  # noqa
from .show import ShowHandler  # noqa
from .exec_ import ExecHandler  # noqa
from .sub import SubHandler  # noqa
from .set_ import SetHandler  # noqa
