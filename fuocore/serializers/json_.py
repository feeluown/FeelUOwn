import json
from .python import PythonSerializer


class JsonSerializer(PythonSerializer):

    def serialize(self, obj):
        dict_ = super().serialize(obj)
        return json.dumps(dict_)
