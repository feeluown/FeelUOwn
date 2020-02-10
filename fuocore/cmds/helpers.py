"""
fuocore.cmds.helper
~~~~~~~~~~~~~~~~~~~

良好的用文字展示一个对象

展示的时候需要注意以下几点：
1. 让 awk、grep 等 shell 工具容易处理

TODO: 让代码长得更好看
"""

import json
from typing import Optional, Generator, Union

from fuocore.models import BaseModel
from fuocore.utils import WideFormatter


class RenderNode:
    def __init__(self, model: BaseModel, **options):
        self.model = model
        self.options = options


def dict_walker(indict: dict, path: Optional[list] = None) -> Generator:
    path = path[:] if path else []
    if isinstance(indict, dict):
        for key, value in indict.items():
            if isinstance(value, dict):
                for d in dict_walker(value, path + [key]):
                    yield d
            elif isinstance(value, list) or isinstance(value, tuple):
                if not value:
                    yield path + [key] + [0], None
                for i, v in enumerate(value):
                    for d in dict_walker(v, path + [key] + [i]):
                        yield d
            else:
                yield path + [key], value
    else:
        yield path, indict


def set_item_by_path(obj: dict, path: list, value):
    for key, son in zip([None] + path, path + [None]):
        if key is None or son is None:
            continue
        if isinstance(obj, dict):
            obj = obj.setdefault(key, [] if isinstance(son, int) else {})
        elif isinstance(obj, list):
            obj.extend([[] if isinstance(son, int) else {}
                        for _ in range(key - len(obj) + 1)])
            obj = obj[key]

    if isinstance(path[-1], int):
        obj.extend([set() for _ in range(path[-1] - len(obj) + 1)])
    obj[path[-1]] = value


class Serializer:
    @staticmethod
    def _render(obj: BaseModel, **options) -> Union[str, dict]:
        raise NotImplementedError

    @classmethod
    def _serialize(cls, indict) -> dict:
        is_complete = False

        output = {}
        obj = indict
        while not is_complete:
            is_complete = True
            for elem in dict_walker(obj):
                path, value = elem

                rendered = None
                if isinstance(value, RenderNode):
                    rendered = cls._render(value.model, **value.options)
                elif isinstance(value, BaseModel):
                    rendered = cls._render(value)

                if rendered:
                    set_item_by_path(output, path, rendered)
                    is_complete = False
                else:
                    set_item_by_path(output, path, value)
            obj = output

        return obj

    def serialize(self, data: Union[RenderNode, BaseModel, dict]) -> dict:
        return self._serialize({"root": data})["root"]


class PlainSerializer(Serializer):
    @staticmethod
    def _render(obj: BaseModel, **options) -> Union[str, dict]:
        if options.get("brief", True):
            return {"uri": str(obj), "info": obj.to_str(**options)}
        return obj.to_dict(**options)


class JsonSerializer(Serializer):
    @staticmethod
    def _render(obj: BaseModel, **options) -> Union[str, dict]:
        return obj.to_dict(**options)


class Emitter:
    def emit(self, data: dict) -> str:
        raise NotImplementedError


class JsonEmitter(Emitter):
    def emit(self, data: dict) -> str:
        return json.dumps(data, indent=4, ensure_ascii=False)


class PlainEmitter(Emitter):
    formatter = WideFormatter()

    @classmethod
    def _list_g(cls, obj, indent='') -> Generator:
        uri_len = max(map(lambda x: len(x["uri"]) if isinstance(x, dict) else 0, obj)) \
            if obj else 0
        for item in obj:
            if isinstance(item, (str, int, float)):
                yield "\t{}".format(item)
            elif isinstance(item, dict):
                yield cls.formatter.format(
                    "{indent}{uri:+{uri_length}}\t# {info}",
                    **item, uri_length=uri_len, indent=indent)

    def _emit(self, data: dict) -> Generator:
        if isinstance(data, dict):
            key_length = max(map(len, data.keys())) + 1
            for k, v in data.items():
                value = None
                if isinstance(v, (str, int, float)):
                    value = v
                elif isinstance(v, dict):
                    value = "{uri}\t# {info}".format(**v)
                if value is not None:
                    yield "{k:{key_length}}\t{value}".format(k=k + ":", value=value,
                                                             key_length=key_length)
            for k, v in data.items():
                if isinstance(v, list):
                    yield "{}::".format(k)
                    yield from self._list_g(v, indent="\t")
        elif isinstance(data, list):
            yield from self._list_g(data)

    def emit(self, data: dict) -> str:
        return "\n".join(self._emit(data))


class Dumper:
    _serializer = None
    _emitter = None

    def __init__(self):
        self._serializer_instance = self._serializer()
        self._emitter_instance = self._emitter()

    def dump(self, data: Union[BaseModel, RenderNode, list, str, dict]):
        if isinstance(data, str):
            return data
        if isinstance(data, BaseModel):
            data = RenderNode(data, brief=False)
        serialized = self._serializer_instance.serialize(data)
        return self._emitter().emit(serialized)


class JsonDumper(Dumper):
    _serializer = JsonSerializer
    _emitter = JsonEmitter


class PlainDumper(Dumper):
    _serializer = PlainSerializer
    _emitter = PlainEmitter


json_dumper = JsonDumper()
plain_dumper = PlainDumper()


def get_dumper(dumper_type: str) -> Dumper:
    if dumper_type == "json":
        return json_dumper
    elif dumper_type == "plain":
        return plain_dumper
    else:
        raise ValueError
