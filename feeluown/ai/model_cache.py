from functools import lru_cache

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

    def __init__(self, maxsize: int = 256):
        self._seed_models: dict[str, BaseModel] = {}
        self._libraries = {}
        self._model_get = lru_cache(maxsize=maxsize)(self._model_get_uncached)

    def set_model(self, model: BaseModel):
        self._seed_models[reverse(model)] = model

    def clear(self):
        self._seed_models.clear()
        self._libraries.clear()
        self._model_get.cache_clear()

    def model_get(self, library, uri: str) -> BaseModel:
        model = parse_model_uri(uri)
        cache_key = reverse(model)

        seeded_model = self._seed_models.get(cache_key)
        if seeded_model is not None:
            return seeded_model

        if library is None:
            raise RuntimeError("library is required on cache miss")
        library_key = id(library)
        self._libraries[library_key] = library
        return self._model_get(
            library_key,
            model.source,
            ModelType(model.meta.model_type),
            model.identifier,
        )

    def _model_get_uncached(
        self,
        library_key: int,
        source: str,
        model_type: ModelType,
        identifier: str,
    ) -> BaseModel:
        library = self._libraries[library_key]
        return library.model_get(source, model_type, identifier)
