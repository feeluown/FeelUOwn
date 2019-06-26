import os
import logging
import random

from fuocore.models import ModelType
from fuocore.protocol import ModelParser, get_url
from feeluown.consts import COLLECTIONS_DIR

logger = logging.getLogger(__name__)


class Collection:

    def __init__(self, fpath, parser):
        # TODO: 以后考虑添加 identifier 字段，identifier
        # 字段应该尽量设计成可以跨电脑使用
        self.fpath = fpath
        self._parser = parser

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
                model = self._parser.parse_line(line)
                if model is not None and \
                   model.meta.model_type == ModelType.song:
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
        has_coll = False
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
                filepath = os.path.join(directory, filename)
                coll = Collection(filepath, self.model_parser)
                # TODO: 可以调整为并行
                coll.load()
                has_coll = True
                yield coll

        if not has_coll:
            fpath = self.gen_defualt_fuo()
            coll = Collection(fpath, self.model_parser)
            coll.load()
            yield coll

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
