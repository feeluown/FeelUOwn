from collections import OrderedDict

from feeluown.library import BaseModel, ModelType, parse_line, reverse


class ModelLRUCache:
    """Session scoped cache for resolving model URI to model objects."""

    def __init__(self, maxsize: int = 256):
        self._maxsize = maxsize
        self._items: OrderedDict[str, BaseModel] = OrderedDict()

    def get(self, uri: str) -> BaseModel | None:
        model = self._items.get(uri)
        if model is not None:
            self._items.move_to_end(uri)
        return model

    def set(self, uri: str, model: BaseModel):
        self._items[uri] = model
        self._items.move_to_end(uri)
        while len(self._items) > self._maxsize:
            self._items.popitem(last=False)

    def set_model(self, model: BaseModel):
        self.set(reverse(model), model)

    def clear(self):
        self._items.clear()

    def model_get(
        self,
        library,
        uri: str,
        expected_type: ModelType | None = None,
    ) -> BaseModel:
        uri = uri.strip()
        if not uri:
            raise ValueError("model URI is required")
        try:
            model, path = parse_line(uri)
        except Exception as e:
            raise ValueError("invalid model URI") from e
        if path:
            raise ValueError("model URI must not include path")
        model_type = ModelType(model.meta.model_type)
        if expected_type is not None and model_type != expected_type:
            raise ValueError(
                f"expected {expected_type.name} URI, got {model_type.name}"
            )

        cache_key = reverse(model)
        cached = self.get(cache_key)
        if cached is not None:
            return cached

        if library is None:
            raise RuntimeError("library is required on cache miss")
        fetched = library.model_get(model.source, model_type, model.identifier)
        self.set(cache_key, fetched)
        return fetched
