from collections import OrderedDict
from threading import Lock

from feeluown.library import BaseModel, ModelType, parse_line, reverse


def parse_model_uri(uri: str) -> BaseModel:
    uri = uri.strip()
    if not uri:
        raise ValueError("model URI is required")
    try:
        model, path = parse_line(uri)
    except Exception as e:
        raise ValueError("invalid model URI") from e
    if path:
        raise ValueError("model URI must not include path")
    return model


class ModelCache:
    """Session scoped cache for resolving model URI to model objects."""

    def __init__(self, library, maxsize: int = 256):
        if maxsize < 0:
            raise ValueError("maxsize must not be negative")
        self._library = library
        self._maxsize = maxsize
        self._models: OrderedDict[str, BaseModel] = OrderedDict()
        self._lock = Lock()

    def set_model(self, model: BaseModel):
        with self._lock:
            self._set(reverse(model), model)

    def get(self, uri: str) -> BaseModel:
        model = parse_model_uri(uri)
        cache_key = reverse(model)

        with self._lock:
            cached_model = self._models.get(cache_key)
            if cached_model is not None:
                self._models.move_to_end(cache_key)
                return cached_model

        if self._library is None:
            raise RuntimeError("library is required on cache miss")
        fetched_model = self._library.model_get(
            model.source,
            ModelType(model.meta.model_type),
            model.identifier,
        )

        with self._lock:
            cached_model = self._models.get(cache_key)
            if cached_model is not None:
                self._models.move_to_end(cache_key)
                return cached_model
            self._set(cache_key, fetched_model)
        return fetched_model

    def _set(self, uri: str, model: BaseModel):
        self._models[uri] = model
        self._models.move_to_end(uri)
        while len(self._models) > self._maxsize:
            self._models.popitem(last=False)
