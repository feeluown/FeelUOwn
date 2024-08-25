from feeluown.library import BaseModel, reverse

from .typename import attach_typename, get_type_by_name, model_cls_list
from .base import Serializer, SerializerMeta, DeserializerError


class PythonDeserializer:
    _mapping = {}

    def deserialize(self, obj):
        if isinstance(obj, dict):
            typename = obj['__type__']
            deserializer_cls = self.get_deserializer_cls(typename)
            return deserializer_cls().deserialize(obj)
        elif isinstance(obj, list):
            return [self.deserialize(each) for each in obj]
        if isinstance(obj, (str, int, float, type(None))):
            return obj
        raise DeserializerError(f'no deserializer for type:{type(obj)}')

    @classmethod
    def get_deserializer_cls(cls, typename):
        clz = get_type_by_name(typename)
        if clz is None:
            raise DeserializerError(f'no deserializer for type:{typename}')
        for obj_clz, deserializer_cls in cls._mapping.items():
            if obj_clz == clz:
                return deserializer_cls
        raise DeserializerError(f'no deserializer for type:{clz}')


class ModelDeserializer(PythonDeserializer, metaclass=SerializerMeta):
    class Meta:
        types = model_cls_list

    def deserialize(self, obj):
        from typing import Annotated
        from pydantic import RootModel
        from feeluown.library.models import BeforeValidator, model_validate

        model_cls = get_type_by_name(obj['__type__'])

        class M(RootModel):
            root: Annotated[model_cls, BeforeValidator(model_validate)]

        # return M.model_validate(obj).root
        return model_cls.model_validate(obj)


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
        fields = [field for field in model.model_fields
                  if ((field not in BaseModel.model_fields)
                      or field in ('identifier', 'source', 'state'))]
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
