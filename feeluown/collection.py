import itertools
import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path

import tomlkit

from feeluown.models.uri import resolve, reverse, ResolverNotFound, \
    ResolveFailed, ModelExistence
from feeluown.consts import COLLECTIONS_DIR

logger = logging.getLogger(__name__)

COLL_LIBRARY_IDENTIFIER = 'library'
# for backward compat, we should never change these filenames
LIBRARY_FILENAME = f'{COLL_LIBRARY_IDENTIFIER}.fuo'

TOML_DELIMLF = "+++\n"


class CollectionType(Enum):
    sys_library = 16

    mixed = 8


class Collection:

    def __init__(self, fpath):
        # TODO: 以后考虑添加 identifier 字段，identifier
        # 字段应该尽量设计成可以跨电脑使用
        self.fpath = fpath

        # these variables should be inited during loading
        self.type = None
        self.name = None
        self.models = []
        self.updated_at = None
        self.created_at = None
        self.description = None
        self._has_nonexistent_models = False

        #: tomkit.toml_document.Document
        self._metadata = None

    def load(self):
        """解析文件，初始化自己"""
        self.models = []
        filepath = Path(self.fpath)
        name = filepath.stem
        stat_result = filepath.stat()
        self.updated_at = datetime.fromtimestamp(stat_result.st_mtime)
        self.name = name
        if name == COLL_LIBRARY_IDENTIFIER:
            self.type = CollectionType.sys_library
        else:
            self.type = CollectionType.mixed

        # parse file content
        with filepath.open(encoding='utf-8') as f:
            first = f.readline()
            lines = []
            if first == TOML_DELIMLF:
                is_valid = True
                for line in f:
                    if line == TOML_DELIMLF:
                        break
                    else:
                        lines.append(line)
                else:
                    logger.warning('the metadata is invalid, will ignore it')
                    is_valid = False
                if is_valid is True:
                    toml_str = ''.join(lines)
                    metadata = tomlkit.parse(toml_str)
                    self._loads_metadata(metadata)
                    lines = []
            else:
                lines.append(first)

            for line in itertools.chain(lines, f):
                if not line.strip():  # ignore empty lines
                    continue
                try:
                    model = resolve(line)
                except ResolverNotFound:
                    logger.warning('resolver not found for line:%s', line)
                    model = None
                except ResolveFailed:
                    logger.warning('invalid line: %s', line)
                    model = None
                if model is not None:
                    if model.exists is ModelExistence.no:
                        self._has_nonexistent_models = True
                    self.models.append(model)

    def add(self, model):
        """add model to collection

        :param model: :class:`feeluown.models.BaseModel`
        :return: True means succeed, False means failed
        """
        if model not in self.models:
            line = reverse(model, as_line=True)
            with open(self.fpath, 'r+', encoding='utf-8') as f:
                content = f.read()
                parts = content.split(TOML_DELIMLF, maxsplit=2)
                body = parts[-1]
                f.seek(0, 0)
                self._write_metadata_if_needed(f)
                f.write(f'{line}\n{body}')
                f.truncate()
            self.models.insert(0, model)
        return True

    def remove(self, model):
        if model in self.models:
            url = reverse(model)
            with open(self.fpath, 'r+', encoding='utf-8') as f:
                content = f.read()
                parts = content.split(TOML_DELIMLF, maxsplit=2)
                body = parts[-1]
                lines = []
                for line in body.split('\n'):
                    if line.startswith(url):
                        continue
                    if line:
                        lines.append(line)

                f.seek(0)
                self._write_metadata_if_needed(f)
                f.write('\n'.join(lines))
                f.truncate()
                # 确保最后写入一个换行符，让文件更加美观
                if lines and not lines[-1].endswith('\n'):
                    f.write('\n')
            self.models.remove(model)
        return True

    def on_provider_added(self, provider):
        if not self._has_nonexistent_models:
            return
        for i, model in enumerate(self.models.copy()):
            if model.exists is ModelExistence.no and model.source == provider.identifier:
                model_cls = provider.get_model_cls(model.meta.model_type)
                new_model = model_cls(model)
                new_model.exists = ModelExistence.unknown
                # TODO: emit data changed signal
                self.models[i] = new_model

    def on_provider_removed(self, provider):
        for model in self.models:
            if model.source == provider.identifier:
                model.exists = ModelExistence.no
                self._has_nonexistent_models = True

    def _loads_metadata(self, metadata):
        self._metadata = metadata
        self.created_at = metadata.get('created')
        self.updated_at = metadata.get('updated', self.updated_at)
        self.name = metadata.get('title', self.name)
        self.description = metadata.get('description')

    def _write_metadata_if_needed(self, f):
        # write metadata only if it had before
        if self._metadata:
            self.updated_at = self._metadata['updated'] = datetime.now()
            f.write(TOML_DELIMLF)
            f.write(tomlkit.dumps(self._metadata))
            f.write('\n')
            f.write(TOML_DELIMLF)


class CollectionManager:
    def __init__(self, app):
        self._app = app
        self._library = app.library

    def scan(self):
        """
        scan collections directories for valid fuo files, yield
        Collection instance for each file.
        """
        default_fpaths = []
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
                if filename in ('Songs.fuo', 'Albums.fuo', 'Artists.fuo', 'Videos.fuo'):
                    default_fpaths.append(filepath)
                    continue
                coll = Collection(filepath)
                coll.load()
                self._app.library.provider_added.connect(coll.on_provider_added)
                self._app.library.provider_removed.connect(coll.on_provider_removed)
                yield coll

        fpath = self.generate_library_coll_if_needed(default_fpaths)
        coll = Collection(fpath)
        coll.load()
        self._app.library.provider_added.connect(coll.on_provider_added)
        self._app.library.provider_removed.connect(coll.on_provider_removed)
        yield coll

    def generate_library_coll_if_needed(self, default_fpaths):
        library_fpath = os.path.join(COLLECTIONS_DIR, LIBRARY_FILENAME)
        if os.path.exists(library_fpath):
            if default_fpaths:
                paths_str = ','.join(default_fpaths)
                logger.warning(f'{paths_str} and {library_fpath} '
                               'should not exist at the same time')
                logger.warning(f'{paths_str} are ignored')
            return library_fpath

        logger.info('Generating collection library')
        lines = [TOML_DELIMLF,
                 'title = "Library"',
                 TOML_DELIMLF]
        if default_fpaths:
            for fpath in default_fpaths:
                with open(fpath) as f:
                    for line in f:
                        if line.startswith('fuo://'):
                            lines.append(line)
        with open(library_fpath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        # backup old sys collections if they exists
        for fpath in default_fpaths:
            dirname = os.path.dirname(fpath)
            filename = os.path.basename(fpath)
            filename += '.bak'
            new_fpath = os.path.join(dirname, filename)
            logger.info(f'Rename {fpath} to {new_fpath}')
            os.rename(fpath, new_fpath)
        return library_fpath
