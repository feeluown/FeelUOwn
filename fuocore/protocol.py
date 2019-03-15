import asyncio
import logging
import re

from fuocore.aio_tcp_server import TcpServer
from fuocore.models import ModelType

logger = logging.getLogger(__name__)

__all__ = ('ModelParser', 'FuoProcotol')


TYPE_NS_MAP = {
    ModelType.song: 'songs',
    ModelType.artist: 'artists',
    ModelType.album: 'albums',
    ModelType.playlist: 'playlists',
    ModelType.user: 'users',
    ModelType.lyric: 'lyrics',
}
URL_SCHEME = 'fuo'
NS_TYPE_MAP = {
    value: key
    for key, value in TYPE_NS_MAP.items()
}


def get_url(model):
    source = model.source
    ns = TYPE_NS_MAP[model.meta.model_type]
    identifier = model.identifier
    return 'fuo://{}/{}/{}'.format(source, ns, identifier)


class ModelParser:
    """
    XXX: 名字叫做 Parser 可能不是很合适？这里可能包含类似 Tokenizor 的功能。
    """

    def __init__(self, library):
        """
        :param library: 音乐库
        """
        self._library = library

    def parse_line(self, line):
        # pylint: disable=too-many-locals
        if not line.startswith('fuo://'):
            return None
        parts = line.split('#')
        if len(parts) == 2:
            url, desc = parts
        else:
            url, desc = parts[0], ''
        source_list = [provider.identifier for provider in self._library.list()]
        ns_list = list(TYPE_NS_MAP.values())
        p = re.compile(r'^fuo://({})/({})/(\w+)$'
                       .format('|'.join(source_list), '|'.join(ns_list)))
        m = p.match(url.strip())
        if not m:
            logger.warning('invalid model url')
            return None
        source, ns, identifier = m.groups()
        provider = self._library.get(source)
        Model = provider.get_model_cls(NS_TYPE_MAP[ns])
        if ns == 'songs':
            data = ModelParser.parse_song_desc(desc.strip())
            model = Model.create_by_display(identifier=identifier, **data)
        else:
            model = Model.get(identifier)
        return model

    def gen_line(self, model):
        """dump model to line"""
        line = get_url(model)
        if model.meta.model_type == ModelType.song:
            desc = self.gen_song_desc(model)
            line += '\t# '
            line += desc
        return line

    @classmethod
    def gen_song_desc(cls, song):
        return '{} - {} - {} - {}'.format(
            song.title_display,
            song.artists_name_display,
            song.album_name_display,
            song.duration_ms_display
        )

    @classmethod
    def parse_song_desc(cls, desc):
        values = desc.split(' - ')
        if len(values) < 4:
            values.extend([''] * (4 - len(values)))
        return {
            'title': values[0],
            'artists_name': values[1],
            'album_name': values[2],
            'duration_ms': values[3]
        }


class FuoProtocol:
    """fuo 控制协议

    TODO: 将命令的解析逻辑放在这个类里来实现
    """
    def __init__(self, *, library, player, playlist, live_lyric):
        self._library = library
        self._player = player
        self._playlist = playlist
        self._live_lyric = live_lyric

    async def handle(self, conn, addr):
        event_loop = asyncio.get_event_loop()
        await event_loop.sock_sendall(conn, b'OK feeluown 1.0.0\n')
        while True:
            command = b''
            try:
                max_bytes = 1024 * 1024
                per_bytes = 256
                while len(command) < max_bytes:
                    part = await event_loop.sock_recv(conn, per_bytes)
                    command += part
                    if len(part) < per_bytes:
                        break
                else:
                    logger.warning('The length of command should be less than 1K')
            except ConnectionResetError:
                logger.debug('客户端断开连接')
                break
            command = command.decode().strip()
            # NOTE: we will never recv empty byte unless
            # client close the connection
            if not command:
                conn.close()
                break
            logger.debug('RECV: %s', command)
            cmd = CmdParser.parse(command)
            msg = exec_cmd(cmd,
                           library=self._library,
                           player=self._player,
                           playlist=self._playlist,
                           live_lyric=self._live_lyric)
            await event_loop.sock_sendall(conn, bytes(msg, 'utf-8'))

    def run_server(self):
        port = 23333
        host = '0.0.0.0'
        event_loop = asyncio.get_event_loop()
        event_loop.create_task(
            TcpServer(host, port, handle_func=self.handle).run())
        logger.info('Fuo daemon run at {}:{}'.format(host, port))


from fuocore.cmds import exec_cmd, CmdParser
