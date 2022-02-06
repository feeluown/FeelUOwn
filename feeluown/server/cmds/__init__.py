import logging

from feeluown.serializers import serialize
from feeluown.server.data_structure import Request, Response

from .base import cmd_handler_mapping
from .excs import CmdException

logger = logging.getLogger(__name__)


class Cmd:
    """
    TODO: Maybe we should remove this class and use Request instead.
    """
    def __init__(self, action, *args, options=None):
        self.action = action
        self.args = args
        self.options = options or {}

    def __str__(self):
        return f'action:{self.action} args:{self.args}'


class CmdResolver:
    def __init__(self, cmd_handler_mapping_):
        self.cmd_handler_mapping = cmd_handler_mapping_

    def get_handler(self, cmd):
        return self.cmd_handler_mapping.get(cmd)


cmd_resolver = CmdResolver(cmd_handler_mapping)


_REGISTERED = False


def register_feeluown_serializers():
    # pylint: disable=unused-import,import-outside-toplevel
    from feeluown.serializers.app import (  # noqa
        AppPythonSerializer,
        AppPlainSerializer
    )
    global _REGISTERED  # pylint: disable=global-statement
    _REGISTERED = True


def handle_request(req: Request, app, session=None):
    """
    :type req: feeluown.server.rpc.Request
    """
    if not _REGISTERED:
        register_feeluown_serializers()

    cmd = Cmd(req.cmd, *req.cmd_args, options=req.cmd_options)

    ok, body = False, ''
    handler_cls = cmd_resolver.get_handler(cmd.action)
    if handler_cls is None:
        ok, body = False, f"handler for cmd:{req.cmd} not found"
    else:
        try:
            handler = handler_cls(app=app, session=session)
            rv = handler.handle(cmd)
        except CmdException as e:
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
