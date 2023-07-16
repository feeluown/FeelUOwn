"""
本地收藏管理
~~~~~~~~~~~~~
"""
from __future__ import annotations
import base64
from typing import TYPE_CHECKING, Dict

from feeluown.utils.utils import elfhash
from feeluown.gui.widgets.collections import CollectionsModel
from feeluown.collection import CollectionType, Collection

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class CollectionUiManager:
    def __init__(self, app: GuiApp):
        self._app = app
        self.model = CollectionsModel(app)
        self._id_coll_mapping: Dict[str, Collection] = {}

    def get(self, identifier):
        return self._id_coll_mapping.get(identifier, None)

    def get_coll_id(self, coll):
        # TODO: 目前还没想好 collection identifier 计算方法，故添加这个函数
        # 现在把 fpath 当作 identifier 使用，但对外透明
        return elfhash(base64.b64encode(bytes(coll.fpath, 'utf-8')))

    def get_coll_library(self):
        for coll in self._id_coll_mapping.values():
            if coll.type == CollectionType.sys_library:
                return coll
        assert False, "collection 'library' must exists."

    def add(self, collection):
        coll_id = self.get_coll_id(collection)
        assert coll_id not in self._id_coll_mapping, collection.fpath
        self._id_coll_mapping[coll_id] = collection
        self.model.add(collection)

    def remove(self, collection):
        coll_id = self.get_coll_id(collection)
        if coll_id in self._id_coll_mapping:
            self._id_coll_mapping.pop(coll_id)
            self.model.remove(collection)

    def clear(self):
        self._id_coll_mapping.clear()
        self.model.clear()

    def initialize(self):
        self._scan()

    def refresh(self):
        """重新加载本地收藏列表"""
        self.model.clear()
        self._id_coll_mapping.clear()
        self._scan()

    def _scan(self):
        colls = []
        library_coll = None
        for coll in self._app.coll_mgr.scan():
            if coll.type == CollectionType.sys_library:
                library_coll = coll
                continue
            colls.append(coll)
        colls.insert(0, library_coll)
        for coll in colls:
            self.add(coll)
