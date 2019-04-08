import asyncio
import logging
import re

from fuocore.models import ModelType

logger = logging.getLogger(__name__)

__all__ = ('ModelParser',)


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
            model = Model.create_by_display(identifier=identifier)
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


class FuoServerProtocol(asyncio.streams.FlowControlMixin):
    """asyncio-style fuo server protocol

    Implementation reference:

    - asyncio.streams.StreamReaderProtocol
    - aiohttp.web_protocol.RequestHandler
    """
    def __init__(self, loop=None):
        super().__init__(loop)
        self._loop = loop

        # StreamReader provides some convinient file-object-like methods
        # like readline, which is really useful for our implementation.
        self._reader = None  # type: asyncio.StreamReader
        self._writer = None

    async def start(self):
        """connection handler"""
        # we should call drain after each write to do flow control,
        # though it is not so important in this case.
        self._writer.write(b'OK fuo 3.0\r\n')
        await self._writer.drain()
        while not self._connection_lost:
            try:
                line = await self._reader.readline()
            except ConnectionResetError:
                break
            except Exception as e:
                logger.exception('unexpected error.')
            else:
                self._writer.write(b'x\r\n')
                # self._writer.write(b'x'*1024*1024*10)
                await self._writer.drain()
                #self.transport.close()
        print('start finished')

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logger.debug('{} connceted to fuo daemon.'.format(peername))
        self._reader = asyncio.StreamReader(loop=self._loop)
        self._writer = asyncio.StreamWriter(
            transport, self, self._reader, self._loop)
        # Unlike aiohttp RequestHandler, we will never cancel the handler task,
        # our task should die when it is supposed to. For instance, when the
        # client close the connection, StreamReader readline method will
        # raise ConnectionResetErrror, the handler task should
        # catch the exc and exit.
        self._loop.create_task(self.start())

    def connection_lost(self, exc):
        """called when our transport is closed"""
        if self._reader is not None:
            if exc is None:
                self._reader.feed_eof()
            else:
                self._reader.set_exception(exc)
        super().connection_lost(exc)
        # HELP: if you dive into aiohttp RequestHandler or StreamReaderProtocol,
        # you can see that they set reader, writer...almost
        # every thing to None when connection lost. I just dont know why.
        # I have done some experiment, the reader and writer can be
        # gc-collected even if we do not set it to None manually.
        # they can be deleted after protocol(self) is deleted.
        self._reader = None
        self._writer = None

    def data_received(self, data):
        self._reader.feed_data(data)

    def eof_received(self):
        """client has written eof

        Explaination: this means the client will send no more data,
        client has close the socket or shutdown with SHUT_WR/SHUT_RDWR flag.
        If we use tcpdump to do packet capture, we can see a FIN packet.

        For fuo protocol, if client shutdown the write pipe, we believe that
        the client is closing the socket, we will just close the socket,
        send no data any more, even if the last response may not complete.
        """
        return False


from fuocore.cmds import CmdLexer
