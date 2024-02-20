from enum import IntEnum, Enum, IntFlag


class ModelFlags(IntFlag):
    none = 0x00000000

    v1 = 0x00000001
    v2 = 0x00000002

    brief = 0x00000010
    normal = brief | 0x00000020


class ModelType(IntEnum):
    dummy = 0

    song = 1
    artist = 2
    album = 3
    playlist = 4
    lyric = 5
    video = 6

    user = 17
    comment = 18

    none = 128


class MediaFlags(IntFlag):
    not_sure = 0b10000000  # 不确定
    not_exists = 0b00  # 不存在相关资源
    sample = 0b01  # 存在试听片段
    free = 0b10  # 存在免费的完整资源
    vip = 0b100  # 存在资源，不免费，vip 可用
    pay = 0b1000  # 存在资源，不免费，付费可用


class SearchType(Enum):
    pl = 'playlist'
    al = 'album'
    ar = 'artist'
    so = 'song'
    vi = 'video'

    @classmethod
    def parse(cls, obj):
        """get member from object

        :param obj: string or SearchType member
        :return: SearchType member

        >>> SearchType.parse('playlist')
        <SearchType.pl: 'playlist'>
        >>> SearchType.parse(SearchType.pl)
        <SearchType.pl: 'playlist'>
        >>> SearchType.parse('xxx')
        Traceback (most recent call last):
          ...
        ValueError: 'xxx' is not a valid SearchType value
        """
        if isinstance(obj, SearchType):
            return obj

        type_aliases_map = {
            cls.pl: ('playlist', 'pl'),
            cls.al: ('album', 'al'),
            cls.ar: ('artist', 'ar'),
            cls.so: ('song', 'so'),
            cls.vi: ('video', 'vi'),
        }
        for type_, aliases in type_aliases_map.items():
            if obj in aliases:
                return type_
        raise ValueError("'%s' is not a valid SearchType value" % obj)

    @classmethod
    def batch_parse(cls, obj):
        """get list of member from obj

        :param obj: obj can be string, list of string or list of member
        :return: list of member

        >>> SearchType.batch_parse('pl,ar')
        [<SearchType.pl: 'playlist'>, <SearchType.ar: 'artist'>]
        >>> SearchType.batch_parse(['pl', 'ar'])
        [<SearchType.pl: 'playlist'>, <SearchType.ar: 'artist'>]
        >>> SearchType.batch_parse('al')
        [<SearchType.al: 'album'>]
        >>> SearchType.batch_parse(SearchType.al)
        [<SearchType.al: 'album'>]
        >>> SearchType.batch_parse([SearchType.al])
        [<SearchType.al: 'album'>]
        """
        if isinstance(obj, SearchType):
            return [obj]
        if isinstance(obj, str):
            return [cls.parse(s) for s in obj.split(',')]
        return [cls.parse(s) for s in obj]


class AlbumType(Enum):
    """Album type enumeration

    中文解释::

        Single 和 EP 会有一些交集，在展示时，会在一起展示，比如 Singles & EPs。
        Compilation 和 Retrospective 也会有交集，展示时，也通常放在一起，统称“合辑”。

    References:

    1. https://www.zhihu.com/question/22888388/answer/33255107
    2. https://zh.wikipedia.org/wiki/%E5%90%88%E8%BC%AF
    """
    standard = 'standard'

    single = 'single'
    ep = 'EP'

    live = 'live'

    compilation = 'compilation'
    retrospective = 'retrospective'

    @classmethod
    def guess_by_name(cls, name):
        """guess album type by its name"""

        # album name which contains following string are `Single`
        #   1. ' - Single'  6+3=9
        #   2. '(single)'   6+2=8
        #   3. '（single）'  6+2=8
        if 'single' in name[-9:].lower():
            return cls.single

        # ' - EP'
        if 'ep' in name[-5:].lower():
            return cls.ep

        if 'live' in name or '演唱会' in name or \
           '音乐会' in name:
            return cls.live

        # '精选集', '精选'
        if '精选' in name[-3:]:
            return cls.retrospective

        return cls.standard
