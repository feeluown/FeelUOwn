import logging

from fuocore.excs import FuocoreException
from .base import cmd_handler_mapping

from .help import HelpHandler  # noqa
from .status import StatusHandler  # noqa
from .playlist import PlaylistHandler  # noqa
from .player import PlayerHandler  # noqa
from .search import SearchHandler  # noqa
from .show import ShowHandler  # noqa
from .exec_ import ExecHandler  # noqa
from .download import DownloadHandler  # noqa

logger = logging.getLogger(__name__)


class CmdException(FuocoreException):
    pass


class Cmd:
    def __init__(self, action, *args, options=None):
        self.action = action
        self.args = args
        self.options = options

    def __str__(self):
        return 'action:{} args:{}'.format(self.action, self.args)


class CmdResolver:
    def __init__(self, cmd_handler_mapping):
        self.cmd_handler_mapping = cmd_handler_mapping

    def get_handler(self, cmd):
        return self.cmd_handler_mapping.get(cmd)


cmd_resolver = CmdResolver(cmd_handler_mapping)


def exec_cmd(cmd, *args, library, player, playlist, live_lyric):
    """执行命令

    .. note::

        此函数理论上是可以脱离 feeluown 的 App 概念来运行的，
        所以目前这里没有将 app 设计为参数。
        但在实践中，这个设计似乎会让代码可读性变差，是值得探讨的。
    """

    logger.debug('EXEC_CMD: ' + str(cmd))

    handler_cls = cmd_resolver.get_handler(cmd.action)
    if handler_cls is None:
        return False, 'cmd not found!'

    try:
        handler = handler_cls(library=library,
                              player=player,
                              playlist=playlist,
                              live_lyric=live_lyric)
        rv = handler.handle(cmd)
    except Exception:
        logger.exception('handle cmd({}) error'.format(cmd))
        return False, 'internal server error'
    else:
        if rv is None:
            rv = ''
        return True, str(rv)
