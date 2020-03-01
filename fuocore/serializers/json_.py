import json
from .python import PythonSerializer


class JsonSerializer(PythonSerializer):

    def __init__(self, **options):
        dump_options_keys = ['skipkeys', 'ensure_ascii', 'check_circular',
                             'allow_nan', 'cls', 'indent', 'separators',
                             'default', 'sort_keys', ]
        self.dump_options = {}
        for key in dump_options_keys:
            if key in options:
                self.dump_options[key] = options.pop(key)
        super().__init__(**options)

    def serialize(self, obj):
        dict_ = super().serialize(obj)
        return json.dumps(dict_, **self.dump_options)
