from enum import Enum

from .base import BaseModel, ModelType


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


class SearchModel(BaseModel):
    """Search Model

    TODO: support album and artist
    """
    class Meta:
        model_type = ModelType.dummy.value

        # XXX: songs should be a empty list instead of None
        # when there is not song.
        fields = ['q', 'songs', 'playlists', 'artists', 'albums', 'videos']
        fields_no_get = ['q', 'songs', 'playlists', 'artists', 'albums', 'videos']

    def __str__(self):
        return 'fuo://{}?q={}'.format(self.source, self.q)
