import base64
import itertools
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

import tomlkit

from feeluown.consts import COLLECTIONS_DIR
from feeluown.utils.dispatch import Signal
from feeluown.library import resolve, reverse, ResolverNotFound, \
    ResolveFailed, ModelState, CollectionType, ModelType
from feeluown.utils.utils import elfhash

logger = logging.getLogger(__name__)

COLL_LIBRARY_IDENTIFIER = 'library'
COLL_POOL_IDENTIFIER = 'pool'
# for backward compat, we should never change these filenames
LIBRARY_FILENAME = f'{COLL_LIBRARY_IDENTIFIER}.fuo'
POOL_FILENAME = f'{COLL_POOL_IDENTIFIER}.fuo'
DEPRECATED_FUO_FILENAMES = (
    'Songs.fuo', 'Albums.fuo', 'Artists.fuo', 'Videos.fuo'
)

TOML_DELIMLF = "+++\n"


class CollectionAlreadyExists(Exception):
    pass


class Collection:
    """
    TODO: This collection should be moved into local provider.
    """

    def __init__(self, fpath):
        # TODO: 以后考虑添加 identifier 字段，identifier
        # 字段应该尽量设计成可以跨电脑使用
        self.fpath = str(fpath)
        # TODO: 目前还没想好 collection identifier 计算方法，故添加这个函数
        # 现在把 fpath 当作 identifier 使用，但对外透明
        self.identifier = elfhash(base64.b64encode(bytes(self.fpath, 'utf-8')))

        # these variables should be inited during loading
        self.type = None
        self.name = None  # Collection title.
        self.models = []
        self.updated_at = None
        self.created_at = None
        self.description = None
        self._has_nonexistent_models = False

        #: tomkit.toml_document.Document
        self._metadata = None

    def load(self):
        """解析文件，初始化自己"""
        # pylint: disable=too-many-branches
        self.models = []
        filepath = Path(self.fpath)
        name = filepath.stem
        stat_result = filepath.stat()
        self.updated_at = datetime.fromtimestamp(stat_result.st_mtime)
        self.name = name
        if name == COLL_LIBRARY_IDENTIFIER:
            self.type = CollectionType.sys_library
        elif name == COLL_POOL_IDENTIFIER:
            self.type = CollectionType.sys_pool
        else:
            self.type = CollectionType.mixed

        # parse file content
        with filepath.open(encoding='utf-8') as f:
            first = f.readline()
            lines = []
            if first == TOML_DELIMLF:
                is_valid = False
                for line in f:
                    if line == TOML_DELIMLF:
                        is_valid = True
                        break
                    lines.append(line)
                if is_valid is True:
                    toml_str = ''.join(lines)
                    metadata = tomlkit.parse(toml_str)
                    self._loads_metadata(metadata)
                    lines = []
                else:
                    logger.warning('the metadata is invalid, will ignore it')
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
                except ResolveFailed as e:
                    logger.warning('resolve failed, file:%s, line:%s, error:%s',
                                   str(filepath), line, str(e))
                    model = None
                if model is not None:
                    if model.state is ModelState.not_exists:
                        self._has_nonexistent_models = True
                    self.models.append(model)

    def list_latest_n(self, n, model_type=None):
        latest_n = []
        for model in self.models:
            if n <= 0:
                break
            if ModelType(model.meta.model_type) == ModelType(model_type):
                latest_n.append(model)
                n -= 1
        return latest_n

    @classmethod
    def create_empty(cls, fpath, title=''):
        """Create an empty collection."""
        if os.path.exists(fpath):
            raise CollectionAlreadyExists()

        doc = tomlkit.document()
        if title:
            doc.add('title', title)         # type: ignore[arg-type]
        doc.add('created', datetime.now())  # type: ignore[arg-type]
        doc.add('updated', datetime.now())  # type: ignore[arg-type]
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(TOML_DELIMLF)
            f.write(tomlkit.dumps(doc))
            f.write(TOML_DELIMLF)

        coll = cls(fpath)
        coll._loads_metadata(doc)
        coll.type = CollectionType.mixed
        return coll

    def add(self, model):
        """add model to collection

        :param model: :class:`feeluown.library.BaseModel`
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
            if model.state is ModelState.not_exists and \
                    model.source == provider.identifier:
                new_model = resolve(reverse(model, as_line=True))
                # TODO: emit data changed signal
                self.models[i] = new_model
        # TODO: set _has_nonexistent_models to proper value

    def on_provider_removed(self, provider):
        for model in self.models:
            if model.source == provider.identifier:
                model.state = ModelState.not_exists
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
            s = tomlkit.dumps(self._metadata)
            f.write(TOML_DELIMLF)
            f.write(s)
            if not s.endswith('\n'):
                f.write('\n')
            f.write(TOML_DELIMLF)

    def raw_data(self):
        """Return the raw data of the collection file.

        .. versionadded:: 4.1.11
        """
        with open(self.fpath, encoding='utf-8') as f:
            return f.read()

    def overwrite_with_raw_data(self, raw_data):
        """Overwrite the collection file with the provided raw data.

        .. versionadded:: 4.1.11
        """
        with open(self.fpath, 'w', encoding='utf-8') as f:
            f.write(raw_data)
        self.load()


class CollectionManager:

    def __init__(self, app):
        self._app = app
        self.scan_finished = Signal()
        self._library = app.library
        self.default_dir = COLLECTIONS_DIR

        self._id_coll_mapping: Dict[int, Collection] = {}
        self._sys_colls = {}

    def get(self, identifier):
        if identifier in (CollectionType.sys_pool, CollectionType.sys_library):
            return self._sys_colls[identifier]
        return self._id_coll_mapping[int(identifier)]

    def get_coll_library(self):
        for coll in self._id_coll_mapping.values():
            if coll.type == CollectionType.sys_library:
                return coll
        assert False, "collection 'library' must exists."

    def create(self, fname, title) -> Collection:
        first_valid_dir = ''
        for d, exists in self._get_dirs():
            if exists:
                first_valid_dir = d
                break

        assert first_valid_dir, 'there must be a valid collection dir'
        normalized_name = fname.replace(' ', '_')
        fpath = os.path.join(first_valid_dir, normalized_name)
        filepath = f'{fpath}.fuo'
        logger.info(f'Create collection:{title} at {filepath}')
        return Collection.create_empty(filepath, title)

    def remove(self, collection: Collection):
        coll_id = collection.identifier
        if coll_id in self._id_coll_mapping:
            self._id_coll_mapping.pop(coll_id)
            os.remove(collection.fpath)

    def _get_dirs(self, ):
        directorys = [self.default_dir]
        if self._app.config.COLLECTIONS_DIR:
            if isinstance(self._app.config.COLLECTIONS_DIR, list):
                directorys += self._app.config.COLLECTIONS_DIR
            else:
                directorys.append(self._app.config.COLLECTIONS_DIR)
        expanded_dirs = []
        for directory in directorys:
            directory = os.path.expanduser(directory)
            expanded_dirs.append((directory, os.path.exists(directory)))
        return expanded_dirs

    def scan(self):
        colls: List[Collection] = []
        for coll in self._scan():
            if coll.type == CollectionType.sys_library:
                self._sys_colls[CollectionType.sys_library] = coll
            elif coll.type == CollectionType.sys_pool:
                self._sys_colls[CollectionType.sys_pool] = coll
            else:
                colls.append(coll)

        # Before, the collection sys_pool is auto created. Now, it is not created
        # automatically. Only load it if it exists.
        pool_coll = self._sys_colls.get(CollectionType.sys_pool)
        library_coll = self._sys_colls[CollectionType.sys_library]
        if pool_coll is not None:
            colls.insert(0, pool_coll)
        colls.insert(0, library_coll)
        for collection in colls:
            coll_id = collection.identifier
            assert coll_id not in self._id_coll_mapping, collection.fpath
            self._id_coll_mapping[coll_id] = collection
        self.scan_finished.emit()

    def refresh(self):
        self.clear()
        self.scan()

    def listall(self):
        return self._id_coll_mapping.values()

    def clear(self):
        self._id_coll_mapping.clear()

    def _scan(self) -> Iterable[Collection]:
        """Scan collections directories for valid fuo files, yield
        Collection instance for each file.
        """
        default_fpaths = []
        valid_dirs = self._get_dirs()
        for directory, exists in valid_dirs:
            if not exists:
                logger.warning('Collection directory %s does not exist', directory)
                continue
            for filename in os.listdir(directory):
                if not filename.endswith('.fuo'):
                    continue
                filepath = os.path.join(directory, filename)
                if filename in DEPRECATED_FUO_FILENAMES:
                    default_fpaths.append(filepath)
                    continue
                coll = Collection(filepath)
                coll.load()
                self._app.library.provider_added.connect(coll.on_provider_added)
                self._app.library.provider_removed.connect(coll.on_provider_removed)
                yield coll

        fpath, generated = self.generate_library_coll_if_needed(default_fpaths)
        # Avoid to yield a duplicated collection.
        if generated is True:
            coll = Collection(fpath)
            coll.load()
            self._app.library.provider_added.connect(coll.on_provider_added)
            self._app.library.provider_removed.connect(coll.on_provider_removed)
            yield coll

    def generate_library_coll_if_needed(self, default_fpaths):
        """
        :return: (library file path, generated)
        """
        library_fpath = os.path.join(self.default_dir, LIBRARY_FILENAME)
        if os.path.exists(library_fpath):
            if default_fpaths:
                paths_str = ','.join(default_fpaths)
                logger.warning(f'{paths_str} are ignored since {library_fpath} exists')
            return library_fpath, False

        logger.info('Generating collection library')
        lines = [TOML_DELIMLF,
                 'title = "Library"',
                 TOML_DELIMLF]
        if default_fpaths:
            for fpath in default_fpaths:
                with open(fpath, 'r', encoding='utf-8') as f:
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
        return library_fpath, True
