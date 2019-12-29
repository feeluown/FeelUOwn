import logging
import os

from fuocore.models.uri import resolve, reverse, ResolverNotFound, ResolveFailed
from feeluown.consts import COLLECTIONS_DIR

logger = logging.getLogger(__name__)

DEFAULT_COLL_SONGS = 'Songs'
DEFAULT_COLL_ALBUMS = 'Albums'
# for backward compat, we should never change these filenames
SONGS_FILENAME = 'Songs.fuo'
ALBUMS_FILENAME = 'Albums.fuo'


class Collection:

    def __init__(self, fpath):
        # TODO: 以后考虑添加 identifier 字段，identifier
        # 字段应该尽量设计成可以跨电脑使用
        self.fpath = fpath

        self.name = ''
        self.models = []
        self.updated_at = None
        self.created_at = None

    def load(self):
        """解析文件，初始化自己"""
        filepath = self.fpath
        filename = filepath.rsplit('/')[-1]
        name, _ = filename.split('.')
        stat_result = os.stat(filepath)
        self.updated_at = stat_result.st_mtime
        self.name = name
        with open(filepath, encoding='utf-8') as f:
            for line in f:
                try:
                    model = resolve(line)
                except ResolverNotFound:
                    logger.warn('resolver not found for line:%s', line)
                    model = None
                except ResolveFailed:
                    logger.warn('invalid line: %s', line)
                    model = None
                if model is not None:
                    self.models.append(model)

    def add(self, song):
        if song not in self.models:
            line = reverse(song, as_line=True)
            with open(self.fpath, 'r+', encoding='utf-8') as f:
                content = f.read()
                f.seek(0, 0)
                f.write(line + '\n' + content)
            self.models.insert(0, song)
        return True

    def remove(self, song):
        if song in self.models:
            url = reverse(song)
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
                if lines and not lines[-1].endswith('\n'):
                    f.write('\n')
            self.models.remove(song)
        return True


class CollectionManager:
    def __init__(self, app):
        self._app = app
        self._library = app.library

    def scan(self):
        has_default_songs = False
        has_default_albums = False
        directorys = [COLLECTIONS_DIR]
        if self._app.config.COLLECTIONS_DIR:
            if isinstance(self._app.config.COLLECTIONS_DIR, list):
                directorys += self._app.config.COLLECTIONS_DIR
            else:
                directorys.append(self._app.config.COLLECTIONS_DIR)
        for directory in directorys:
            directory = os.path.expanduser(directory)
            if not os.path.exists(directory):
                logger.warning('Collection Dir:{} does not exist.'.format(directory))
                continue
            for filename in os.listdir(directory):
                if not filename.endswith('.fuo'):
                    continue
                if filename == SONGS_FILENAME:
                    has_default_songs = True
                elif filename == ALBUMS_FILENAME:
                    has_default_albums = True
                filepath = os.path.join(directory, filename)
                coll = Collection(filepath)
                # TODO: 可以调整为并行
                coll.load()
                yield coll

        default_fpaths = []
        if not has_default_songs:
            default_fpaths.append(self.gen_default_songs_fuo())
        if not has_default_albums:
            default_fpaths.append(self.gen_default_albums_fuo())
        for fpath in default_fpaths:
            coll = Collection(fpath)
            coll.load()
            yield coll

    @classmethod
    def gen_default_songs_fuo(cls):
        logger.info('正在生成默认的本地收藏集 - Songs')
        default_fpath = os.path.join(COLLECTIONS_DIR, SONGS_FILENAME)
        if not os.path.exists(default_fpath):
            with open(default_fpath, 'w', encoding='utf-8') as f:
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
        return default_fpath

    @classmethod
    def gen_default_albums_fuo(cls):
        logger.info('正在生成默认的本地收藏集 - Albums')
        albums_fpath = os.path.join(COLLECTIONS_DIR, ALBUMS_FILENAME)
        if not os.path.exists(albums_fpath):
            with open(albums_fpath, 'w', encoding='utf-8') as f:
                lines = [
                    'fuo://xiami/albums/1194678626     # 脱掉高跟鞋 世界巡回演唱会',
                    'fuo://xiami/albums/32623          # 理性与感性 作品音乐会',
                    'fuo://netease/albums/18878        # OK - 张震岳',
                ]
                f.write('\n'.join(lines))
        return albums_fpath
