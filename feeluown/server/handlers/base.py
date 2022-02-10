from typing import Dict, Type, TypeVar

from feeluown.server.session import SessionLike

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

    def __init__(self, app, session: SessionLike):
        """
        暂时不确定 session 应该设计为什么样的结构。当前主要是为了将它看作一个
        subscriber。
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
