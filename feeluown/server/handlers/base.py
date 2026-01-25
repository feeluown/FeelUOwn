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
        It’s not yet determined what structure the session should have.
        Currently it’s mainly considered as a subscriber.

        Most handlers do not need to use the session object;
        at present only SubHandler treats the session as a subscriber.
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
