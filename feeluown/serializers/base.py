import copy


class SerializerError(Exception):
    """
    this error will be raised when

    * Serializer initialization failed
    * Serializer not found
    * Serializer serialization failed
    """
    pass


class Serializer:
    """Serializer abstract base class

    The subclass MUST has an class attribute `_mapping` if we want to
    get_serializer_cls method, it should store the mapping relation
    between Object-Class and Serializer-Class.
    For example::

        {
            int: IntSerializer,
            SongModel: ModelSerializer,
        }

    the subclass also should implement `serialize` method.

    See JsonSerializer for more details.
    """

    def __init__(self, **options):
        """
        Subclass should validate and parse options by themselves, here,
        we list three commonly used options.

        as_line is a *format* option:

        - as_line: line format of a object (mainly designed for PlainSerializer)

        brief and fetch are *representation* options:

        - brief: a minimum human readable representation of the object.
          we hope that people can *identify which object it is* through
          this representation.
          For example, if an object has ten attributes, this representation
          may only contain three attributes.

        - fetch: if this option is specified, the attribute value
          should be authoritative.
        """
        self.options = copy.deepcopy(options)

    def serialize(self, obj):
        serializer_cls = self.get_serializer_cls(obj)
        return serializer_cls(**self.options).serialize(obj)

    @classmethod
    def get_serializer_cls(cls, model):
        model = try_cast_model_to_v1(model)
        for model_cls, serialize_cls in cls._mapping.items():
            # FIXME: remove me when model v2 has its own serializer
            if isinstance(model, model_cls):
                return serialize_cls
        raise SerializerError("no serializer for {}".format(model))


class SerializerMeta(type):
    def __new__(cls, name, bases, attrs):
        """magic

        TODO: add comments and error handling
        """
        Meta = attrs.pop('Meta', None)
        mapping = attrs.pop('_mapping', None)
        for base in bases:
            if Meta is None and hasattr(base, 'Meta'):
                Meta = base.Meta
            if mapping is None and hasattr(base, '_mapping'):
                mapping = base._mapping
        klass = type.__new__(cls, name, bases, attrs)
        if Meta:
            for type_ in Meta.types:
                mapping[type_] = klass
            fields = getattr(Meta, 'fields', None)
            if fields is not None:
                klass._declared_fields = fields

            # ModelPlainSerializer can have line_fmt attribute
            line_fmt = getattr(Meta, 'line_fmt', None)
            if line_fmt is not None:
                klass._line_fmt = line_fmt
        return klass


class SimpleSerializerMixin(Serializer):

    def serialize(self, obj):
        """
        please ensure you have implemented `_get_items` and
        `serialize_items` method
        """
        items = self._get_items(obj)
        return self.serialize_items(items)


def try_cast_model_to_v1(model):
    from feeluown.library import BaseModel
    from feeluown.fuoexec import _exec_globals

    if isinstance(model, BaseModel):
        app = _exec_globals.get('app')
        if app is not None:
            model = app.library.cast_model_to_v1(model)
            return model
    return model
