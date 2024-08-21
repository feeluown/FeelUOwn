from feeluown.library import BaseModel, reverse

from .typename import attach_typename
from .base import Serializer, SerializerMeta


class PythonSerializer(Serializer):
    _mapping = {}

    def __init__(self, **options):
        super().__init__(**options)

    def serialize_items(self, items):
        json_ = {}
        for key, value in items:
            serializer_cls = PythonSerializer.get_serializer_cls(value)
            serializer = serializer_cls()
            json_[key] = serializer.serialize(value)
        return json_

    @attach_typename
    def serialize(self, obj):
        return super().serialize(obj)


class ModelSerializer(PythonSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (BaseModel, )

    def __init__(self, **options):
        super().__init__(**options)

    def _get_items(self, model):
        modelcls = type(model)
        fields = [field for field in model.__fields__
                  if field not in BaseModel.__fields__]
        # Include properties.
        pydantic_fields = ("__values__", "fields", "__fields_set__",
                           "model_computed_fields", "model_extra",
                           "model_fields_set")
        fields += [prop for prop in dir(modelcls)
                   if isinstance(getattr(modelcls, prop), property)
                   and prop not in pydantic_fields]
        items = [("provider", model.source),
                 ("identifier", str(model.identifier)),
                 ("uri", reverse(model))]
        for field in fields:
            items.append((field, getattr(model, field)))
        return items

    @attach_typename
    def serialize(self, model):
        dict_ = {}
        for field, value in self._get_items(model):
            serializer_cls = self.get_serializer_cls(value)
            value_dict = serializer_cls().serialize(value)
            dict_[field] = value_dict
        return dict_


#######################
# container serializers
#######################


class ListSerializer(PythonSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (list, )

    def serialize(self, list_):
        if not list_:
            return []
        result = []
        for item in list_:
            serializer_cls = PythonSerializer.get_serializer_cls(item)
            serializer = serializer_cls()
            result.append(serializer.serialize(item))
        return result

    def serialize_search_result_list(self, list_):
        from .objs import SearchPythonSerializer
        serializer = SearchPythonSerializer()
        return [serializer.serialize(model) for model in list_]


####################
# object serializers
####################


class SimpleTypeSerializer(PythonSerializer, metaclass=SerializerMeta):
    class Meta:
        types = (str, int, float, type(None))

    def serialize(self, object):
        return object
