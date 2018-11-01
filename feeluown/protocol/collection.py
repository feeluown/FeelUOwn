import os

from fuocore import ModelType
from fuocore.models import Model

from feeluown.consts import COLLECTIONS_DIR


class Collection(Model):

    def __init__(self, name, items):
        self.name = name
        self.items = items

    @classmethod
    def from_fuofile(cls, filepath):
        filename = filepath.rsplit('/')[-1]
        name, _ = filename.split('.')
        items = []  # (source, model_type, id, desc)
        with open(filepath) as f:
            for line in f:
                if not line.startswith('fuo://'):
                    continue
                url, desc = line.split('#')
                items.append((url.strip(), desc.strip()))
        return cls(name, items)


class CollectionManager:
    def __init__(self, app):
        self._app = app

    def scan(self):
        directorys = self._app.config.COLLECTIONS_DIR + [COLLECTIONS_DIR]
        self._app.collections.clear()
        for directory in directorys:
            directory = os.path.expanduser(directory)
            for filename in os.listdir(directory):
                if not filename.endswith('.fuo'):
                    continue
                filepath = os.path.join(directory, filename)
                coll = Collection.from_fuofile(filepath)
                self._app.collections.add(coll)
