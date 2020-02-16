class Serializer:
    def __init__(self, **options):
        self.options = options
        self.options['as_line'] = options.get('as_line', True)
        self.options['brief'] = options.get('brief', True)
        self.options['fetch'] = options.get('fetch', False)

    def serialize(self, obj):
        serializer_cls = self.get_serializer_cls(obj)
        return serializer_cls(**self.options).serialize(obj)

    @classmethod
    def get_serializer_cls(cls, model):
        for model_cls, serialize_cls in cls._mapping.items():
            if isinstance(model, model_cls):
                return serialize_cls
        # TODO: raise error here.


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
