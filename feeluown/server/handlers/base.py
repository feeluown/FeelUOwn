from typing import Dict, Type, TypeVar, Optional, TYPE_CHECKING

from feeluown.server.session import SessionLike

if TYPE_CHECKING:
    from feeluown.app.server_app import ServerApp


T = TypeVar('T', bound='HandlerMeta')
cmd_handler_mapping: Dict[str, 'HandlerMeta'] = {}


class HandlerMeta(type):
    def __new__(cls: Type[T], name, bases, attrs) -> T:
        klass = type.__new__(cls, name, bases, attrs)
        if 'cmds' in attrs:
            cmds = attrs['cmds']
            if isinstance(cmds, str):
                cmd_handler_mapping[cmds] = klass
            else:
                for cmd in cmds:
                    cmd_handler_mapping[cmd] = klass
        return klass


class AbstractHandler(metaclass=HandlerMeta):
    support_aio_handle = False

    def __init__(self, app: 'ServerApp', session: Optional[SessionLike] = None):
        """
        暂时不确定 session 应该设计为什么样的结构。当前主要是为了将它看作一个
        subscriber。大部分 handler 不需要使用到 session 对像，目前只有 SubHandler
        把 session 当作一个 subscriber 看待。
        """
        self._app = app
        self.session = session

        self.library = app.library
        self.player = app.player
        self.playlist = app.playlist
        self.live_lyric = app.live_lyric

    def handle(self, cmd):
        ...

    async def a_handle(self, cmd):
        ...
