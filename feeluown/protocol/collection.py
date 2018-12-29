import logging
import os
import random

from feeluown.consts import COLLECTIONS_DIR
from .parser import ModelParser


logger = logging.getLogger(__name__)


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
        with open(filepath) as f:
            for line in f:
                model = self._parser.parse_line(line)
                if model is not None:
                    self.models.append(model)


class CollectionManager:
    def __init__(self, app):
        self._app = app
        self._library = app.library

        self.model_parser = ModelParser(self._library)

    def scan(self):
        directorys = self._app.config.COLLECTIONS_DIR + [COLLECTIONS_DIR]
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
            with open(fpath, 'w') as f:
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
