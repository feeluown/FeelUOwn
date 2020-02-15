from fuocore.excs import FuoException

from .formatter import WideFormatter
from .serializers import SONG, ARTIST, ALBUM, USER, PLAYLIST


formatter = WideFormatter()
fmt = formatter.format


class DumpError(FuoException):
    pass


class SequenceDumper:
    def dump(self, list_):
        if not list_:
            return ''
        item0 = list_[0]
        if isinstance(item0, dict):
            uri_length = max(len(item['uri']) for item in list_)
            dump_cls = ModelBaseDumper.get_dumper_cls(item0)
            dumper = dump_cls(as_line=True, uri_length=uri_length)
            text_list = []
            for item in list_:
                text_list.append(dumper.dump(item))
            return '\n'.join(text_list)
        # this may not happen
        return '\n'.join(list_)


class ModelBaseDumper:
    _mapping = {}

    def __init__(self, as_line=True, uri_length=None):
        self._as_line = as_line
        self._uri_length = uri_length

    @classmethod
    def get_dumper_cls(cls, json_):
        type_ = json_.get('type')
        if type_ is None:
            raise DumpError("can't dump json without type key")
        return cls._mapping[type_]

    def dump(self, json_):
        if self._as_line:
            uri_length = self._uri_length
            if uri_length is None:
                uri_length = ''
            text = fmt(self._line_fmt, uri_length=uri_length, **json_)
        else:
            key_length = max(len(key) for key in json_.keys()) + 1
            text_list = []
            tpl = '{key:>%d}:  {value}' % key_length
            list_tpl = '{key:>%d}::' % (key_length - 1)
            for key, value in json_.items():
                if isinstance(value, dict):
                    dumper_cls = ModelBaseDumper.get_dumper_cls(value)
                    dumper = dumper_cls(as_line=True)
                    value_text = dumper.dump(value)
                    text_list.append(fmt(tpl, key=key, value=value_text))
                elif isinstance(value, list):
                    dumper = SequenceDumper()
                    value_text = dumper.dump(value)
                    text_list.append(fmt(list_tpl, key=key))
                    if value_text:
                        padding = ' ' * (key_length + 3)
                        text_list.extend((padding + line
                                          for line in value_text.split('\n')))
                else:
                    line = fmt(tpl, key=key, value=value)
                    text_list.append(line)
            text = '\n'.join(text_list)
        return text


class ModelDumperMeta(type):
    def __new__(cls, name, bases, attrs):
        Meta = attrs.pop('Meta', None)
        klass = type.__new__(cls, name, bases, attrs)
        if Meta:
            line_fmt = getattr(Meta, 'line_fmt', [])
            ModelBaseDumper._mapping[Meta.type_] = klass
            klass._line_fmt = line_fmt
        return klass


class SongDumper(ModelBaseDumper, metaclass=ModelDumperMeta):
    class Meta:
        type_ = SONG
        line_fmt = '{uri:{uri_length}}\t# {title:_18} - {artists_name:_20}'


class AlbumDumper(ModelBaseDumper, metaclass=ModelDumperMeta):
    class Meta:
        type_ = ALBUM
        line_fmt = '{uri:{uri_length}}\t# {name:_18} - {artists_name:_20}'


class ArtistDumper(ModelBaseDumper, metaclass=ModelDumperMeta):
    class Meta:
        type_ = ARTIST
        line_fmt = '{uri:{uri_length}}\t# {name:_40}'


class PlaylistDumper(ModelBaseDumper, metaclass=ModelDumperMeta):
    class Meta:
        type_ = PLAYLIST
        line_fmt = '{uri:{uri_length}}\t# {name:_40}'


class UserDumper(ModelBaseDumper, metaclass=ModelDumperMeta):
    class Meta:
        type_ = USER
        line_fmt = '{uri:{uri_length}}\t# {name:_40}'
