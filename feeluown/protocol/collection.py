import os

from feeluown.consts import COLLECTIONS_DIR
from .parser import ModelParser


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
