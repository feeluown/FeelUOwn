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


class FuoServerProtocol(asyncio.Protocol):
    __slots__ = ()

    def __init__(self, loop=None):
        self._loop = loop
        self.transport = None
        self.cmd_lexer = CmdLexer()

    async def start(self):
        """start communication with client"""
        self.transport.write(b'OK fuo 3.0\r\n')

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logger.debug('{} connceted to fuo daemon.'.format(peername))
        self.transport = transport
        self._loop.create_task(self.start())

    def connection_lost(self, exc):
        self.transport = None

    def pause_write(self):
        pass

    def resume_write(self):
        pass

    def data_received(self, data):
        pass

    def eof_received(self):
        """Client closed the connection"""
        pass


from fuocore.cmds import CmdLexer
