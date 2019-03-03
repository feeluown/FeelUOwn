import asyncio
import logging
import os
import random
import re

from fuocore.aio_tcp_server import TcpServer
from fuocore.models import ModelType
from feeluown.consts import COLLECTIONS_DIR

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
        model = None
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


class FuoProcotol:
    """fuo 控制协议

    TODO: 将这个类的实现移到另外一个模块，而不是放在 __init__.py 中
    TODO: 将命令的解析逻辑放在这个类里来实现
    """
    def __init__(self, app):
        self._app = app
        self._library = app.library
        self._live_lyric = app.live_lyric

    async def handle(self, conn, addr):
        app = self._app
        live_lyric = self._live_lyric

        event_loop = asyncio.get_event_loop()
        await event_loop.sock_sendall(conn, b'OK feeluown 1.0.0\n')
        while True:
            try:
                command = await event_loop.sock_recv(conn, 1024)
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
            msg = exec_cmd(app, live_lyric, cmd)
            await event_loop.sock_sendall(conn, bytes(msg, 'utf-8'))

    def run_server(self):
        port = 23333
        host = '0.0.0.0'
        event_loop = asyncio.get_event_loop()
        event_loop.create_task(
            TcpServer(host, port, handle_func=self.handle).run())
        logger.info('Fuo daemon run in {}:{}'.format(host, port))


class Collection:

    def __init__(self, fpath, parser):
        self.fpath = fpath
        self._parser = parser

        self.name = ''
        self.models = []

    def load(self):
        """解析文件，初始化自己"""
        filepath = self.fpath
        filename = filepath.rsplit('/')[-1]
        name, _ = filename.split('.')
        self.name = name
        with open(filepath, encoding='utf-8') as f:
            for line in f:
                model = self._parser.parse_line(line)
                if model is not None:
                    self.models.append(model)

    def add(self, song):
        if song not in self.models:
            line = self._parser.gen_line(song)
            with open(self.fpath, 'r+', encoding='utf-8') as f:
                content = f.read()
                f.seek(0, 0)
                f.write(line + '\n' + content)
            self.models.insert(0, song)
        return True

    def remove(self, song):
        if song in self.models:
            url = get_url(song)
            with open(self.fpath, 'r+', encoding='utf-8') as f:
                lines = []
                for line in f:
                    if line.startswith(url):
                        continue
                    lines.append(line)
                f.seek(0)
                f.write(''.join(lines))
                f.truncate()
                # 确保最后写入一个换行符，让文件更加美观
                if not lines[-1].endswith('\n'):
                    f.write('\n')
            self.models.remove(song)
        return True


class CollectionManager:
    def __init__(self, app):
        self._app = app
        self._library = app.library

        self.model_parser = ModelParser(self._library)

    def scan(self):
        directorys = self._app.config.COLLECTIONS_DIR or [] + [COLLECTIONS_DIR]
        self._app.collections.clear()
        for directory in directorys:
            directory = os.path.expanduser(directory)
            for filename in os.listdir(directory):
                if not filename.endswith('.fuo'):
                    continue
                filepath = os.path.join(directory, filename)
                coll = Collection(filepath, self.model_parser)
                # TODO: 可以调整为并行
                coll.load()
                self._app.collections.add(coll)

        if not self._app.collections:
            fpath = self.gen_defualt_fuo()
            coll = Collection(fpath, self.model_parser)
            coll.load()
            self._app.collections.add(coll)

    @classmethod
    def gen_defualt_fuo(cls):
        logger.info('正在生成本地默认歌单')
        filenames = [
            '你真棒.fuo',
            '萌萌哒.fuo',
            '一起来 Hack.fuo',
            '今天也要元气满满喔.fuo',
            '正经.fuo',
            '有故事的歌曲.fuo',
        ]
        filename = random.choice(filenames)
        fpath = os.path.join(COLLECTIONS_DIR, filename)
        if not os.path.exists(fpath):
            with open(fpath, 'w', encoding='utf-8') as f:
                lines = [
                    'fuo://netease/songs/16841667  # No Matter What - Boyzone',
                    'fuo://netease/songs/65800     # 最佳损友 - 陈奕迅',
                    'fuo://xiami/songs/3406085     # Love Story - Taylor Swift',
                    'fuo://netease/songs/5054926   # When You Say Noth… - Ronan Keating',
                    'fuo://qqmusic/songs/97773     # 晴天 - 周杰伦',
                    'fuo://qqmusic/songs/102422162 # 给我一首歌的时间 … - 周杰伦,蔡依林',
                    'fuo://xiami/songs/1769834090  # Flower Dance - DJ OKAWARI',
                ]
                f.write('\n'.join(lines))
        return fpath


from feeluown.cmds import exec_cmd, CmdParser
