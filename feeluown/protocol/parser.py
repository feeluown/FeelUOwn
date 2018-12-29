import re

from .helpers import TYPE_NS_MAP, URL_SCHEME, NS_TYPE_MAP


class Cmd:
    def __init__(self, action, *args, **kwargs):
        self.action = action
        self.args = args

    def __str__(self):
        return 'action:{} args:{}'.format(self.action, self.args)


class CmdParser:

    @classmethod
    def parse(cls, cmd_str):
        cmd_str = cmd_str.strip()
        cmd_parts = cmd_str.split(' ', 1)
        if not cmd_parts:
            return None
        return Cmd(*cmd_parts)


class ModelParser:
    """
    XXX: 名字叫做 Parser 可能不是很合适？这里可能包含类似 Tokenizor 的功能。
    """

    def __init__(self, library):
        """
        :param library: 音乐库
        """
        self._library = library

    def parse_line(self, line):
        # pylint: disable=too-many-locals
        if not line.startswith('fuo://'):
            return None
        parts = line.split('#')
        if len(parts) == 2:
            url, desc = parts
        else:
            url, desc = parts[0], ''
        source_list = [provider.identifier for provider in self._library.list()]
        ns_list = list(TYPE_NS_MAP.values())
        p = re.compile(r'^fuo://({})/({})/(\w+)$'
                       .format('|'.join(source_list), '|'.join(ns_list)))
        m = p.match(url.strip())
        if not m:
            raise ValueError('invalid model url')
        source, ns, identifier = m.groups()
        provider = self._library.get(source)
        Model = provider.get_model_cls(NS_TYPE_MAP[ns])
        model = None
        if ns == 'songs':
            data = ModelParser.parse_song_desc(desc.strip())
            model = Model.create_by_display(identifier=identifier, **data)
        return model

    @classmethod
    def parse_song_desc(cls, desc):
        values = desc.split(' - ')
        if len(values) < 4:
            values.extend([''] * (4 - len(values)))
        return {
            'title': values[0],
            'artists_name': values[1],
            'album_name': values[2],
            'duration': values[3]
        }
