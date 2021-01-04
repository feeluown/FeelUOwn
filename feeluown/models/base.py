import logging
import time
from threading import RLock

from enum import IntEnum, Enum

logger = logging.getLogger(__name__)
_NOT_FOUND = object()


class cached_field:
    """like functools.cached_property, but designed for Model

    >>> class User:
    ...     @cached_field()
    ...     def playlists(self):
    ...         return [1, 2]
    ...
    >>> user = User()
    >>> user2 = User()
    >>> user.playlists = None
    >>> user.playlists
    [1, 2]
    >>> user.playlists = [3, 4]
    >>> user.playlists
    [3, 4]
    >>> user2.playlists
    [1, 2]
    """
    def __init__(self, ttl=None):
        self._ttl = ttl
        self.lock = RLock()

    def __call__(self, func):
        self.func = func
        return self

    def __get__(self, obj, owner):
        if obj is None:  # Class.field
            return self

        try:
            # XXX: maybe we can use use a special attribute
            # (such as _cached_{name}) to store the cache value
            # instead of __dict__
            cache = obj.__dict__
        except AttributeError:
            raise TypeError("obj should have __dict__ attribute") from None

        cache_key = '_cache_' + self.func.__name__
        datum = cache.get(cache_key, _NOT_FOUND)
        if self._should_refresh_datum(datum):
            with self.lock:
                # check if another thread filled cache while we awaited lock
                datum = cache.get(cache_key, _NOT_FOUND)
                if self._should_refresh_datum(datum):
                    value = self.func(obj)
                    cache[cache_key] = datum = self._gen_datum(value)
        return datum[1]

    def __set__(self, obj, value):
        cache_key = '_cache_' + self.func.__name__
        obj.__dict__[cache_key] = self._gen_datum(value)

    def _should_refresh_datum(self, datum):
        return (
            datum is _NOT_FOUND or  # not initialized
            datum[1] is None or     # None implies that the value can be refreshed
            datum[0] is not None and datum[0] < time.time()  # expired
        )

    def _gen_datum(self, value):
        if self._ttl is None:
            expired_at = None
        else:
            expired_at = int(time.time()) + self._ttl
        return (expired_at, value)


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


class ModelStage(IntEnum):
    """Model 所处的阶段，有大小关系

    通过 create_by_display 工厂函数创建的实例，实例所处阶段为 display,
    通过构造函数创建的实例，阶段为 inited, 如果 model 已经 get 过，
    则阶段为 gotten.

    目前，主要是 __getattribute__ 方法需要读取 model 所处的阶段，
    避免重复 get model。
    """
    display = 4
    inited = 8
    gotten = 16


class ModelExistence(IntEnum):
    """资源是否真的存在

    在许多音乐平台，当一个歌手、专辑不存在时，它们的接口可能构造一个
    id 为 0, name 为 None 的字典。这类 model.exists 应该被置为 no。

    这个字段不应该被缓存。
    """
    no = -1
    unknown = 0
    yes = 1


class ModelMetadata(object):
    def __init__(self,
                 model_type=ModelType.dummy.value,
                 provider=None,
                 fields=None,
                 fields_display=None,
                 fields_no_get=None,
                 paths=None,
                 allow_get=False,
                 allow_batch=False,
                 **kwargs):
        """Model metadata class

        :param allow_get: if get method is implemented
        :param allow_batch: if list method is implemented
        """
        self.model_type = model_type
        self.provider = provider
        self.fields = fields or []
        self.fields_display = fields_display or []
        self.fields_no_get = fields_no_get or []
        self.paths = paths or []
        self.allow_get = allow_get
        self.allow_batch = allow_batch
        for key, value in kwargs.items():
            setattr(self, key, value)


class display_property:
    """Model 的展示字段的描述器"""

    def __init__(self, name):
        #: display 属性对应的真正属性的名字
        self.name_real = name
        #: 用来存储值的属性名
        self.store_pname = '_display_store_' + name

    def __get__(self, instance, _=None):
        if instance is None:
            return self
        if instance.stage >= ModelStage.inited:
            return getattr(instance, self.name_real)
        return getattr(instance, self.store_pname, '')

    def __set__(self, instance, value):
        setattr(instance, self.store_pname, value)


class ModelMeta(type):
    def __new__(cls, name, bases, attrs):
        # 获取 Model 当前以及父类中的 Meta 信息
        # 如果 Meta 中相同字段的属性，子类的值可以覆盖父类的
        _metas = []
        for base in bases:
            base_meta = getattr(base, '_meta', None)
            if base_meta is not None:
                _metas.append(base_meta)
        Meta = attrs.pop('Meta', None)
        if Meta:
            _metas.append(Meta)

        kind_fields_map = {'fields': [],
                           'fields_display': [],
                           'fields_no_get': [],
                           'paths': []}
        meta_kv = {}  # 实例化 ModelMetadata 的 kv 对
        for _meta in _metas:
            for kind, fields in kind_fields_map.items():
                fields.extend(getattr(_meta, kind, []))
            for k, v in _meta.__dict__.items():
                if k.startswith('_') or k in kind_fields_map:
                    continue
                if k == 'model_type':
                    if ModelType(v) != ModelType.dummy:
                        meta_kv[k] = v
                else:
                    meta_kv[k] = v

        klass = type.__new__(cls, name, bases, attrs)

        # update provider
        provider = meta_kv.pop('provider', None)
        model_type = meta_kv.pop('model_type', ModelType.dummy.value)
        if provider and ModelType(model_type) != ModelType.dummy:
            provider.set_model_cls(model_type, klass)

        fields_all = list(set(kind_fields_map['fields']))
        fields_display = list(set(kind_fields_map['fields_display']))
        fields_no_get = list(set(kind_fields_map['fields_no_get']))
        paths = list(set(kind_fields_map['paths']))

        for field in fields_display:
            setattr(klass, field + '_display', display_property(field))

        # DEPRECATED attribute _meta
        # TODO: remove this in verion 2.3
        klass._meta = ModelMetadata(model_type=model_type,
                                    provider=provider,
                                    fields=fields_all,
                                    fields_display=fields_display,
                                    fields_no_get=fields_no_get,
                                    paths=paths,
                                    **meta_kv)
        # FIXME: theoretically, different provider can share same model,
        # so source field should be a instance attribute instead of class attribute.
        # however, we don't have enough time to fix this whole design.
        klass.source = provider.identifier if provider is not None else None
        # use meta attribute instead of _meta
        klass.meta = klass._meta
        return klass


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


class Model(metaclass=ModelMeta):
    """base class for data models

    Usage::

        class User(Model):
            class Meta:
                fields = ['name', 'title']

        user = UserModel(name='xxx')
        assert user.name == 'xxx'
        user2 = UserModel(user)
        assert user2.name == 'xxx'
    """

    def __init__(self, obj=None, **kwargs):
        # ensure all field are initialized to None
        for field in self.meta.fields:
            setattr(self, field, None)

        # copy fields from obj as many as possible
        if obj is not None:
            for field in obj.meta.fields:
                value = object.__getattribute__(obj, field)
                setattr(self, field, value)
            for field in obj.meta.fields_display:
                field_name = f'{field}_display'
                field_display_prop = getattr(type(self), field_name)
                field_display_prop.__set__(self, getattr(obj, field_name))
            # source should be a instance attribute although it is not temporarily
            self.source = obj.source
            self.stage = obj.stage
            self.exists = obj.exists
        else:
            for field in self.meta.fields:
                setattr(self, field, None)
            #: model 所处阶段。目前，通过构造函数初始化的 model
            # 所处阶段为 inited，通过 get 得到的 model，所处阶段为 gotten，
            # 通过 display 属性构造的 model，所处阶段为 display。
            # 目前，此属性仅为 models 模块使用，不推荐外部依赖。
            self.stage = kwargs.get('stage', ModelStage.inited)
            #: 歌曲是否存在。如果 Model allow_get，但 get 却不能获取到 model，
            # 则该 model 不存在。
            self.exists = kwargs.get('stage', ModelExistence.unknown)

        for k, v in kwargs.items():
            if k in self.meta.fields:
                setattr(self, k, v)

    def __getattribute__(self, name):
        """
        获取 model 某一属性时，如果该属性值为 None 且该属性是 field
        且该属性允许触发 get 方法，这时，我们尝试通过获取 model
        详情来初始化这个字段，于此同时，还会重新给部分 fields 重新赋值。
        """
        cls = type(self)
        cls_name = cls.__name__
        value = object.__getattribute__(self, name)

        if name in ('identifier', 'meta', '_meta', 'stage', 'exists'):
            return value

        if name in cls.meta.fields \
           and name not in cls.meta.fields_no_get \
           and value is None \
           and cls.meta.allow_get \
           and self.stage < ModelStage.gotten \
           and self.exists != ModelExistence.no:

            # debug snippet: show info of the caller that trigger the model.get call
            #
            # import inspect
            # frame = inspect.currentframe()
            # caller = frame.f_back
            # logger.info(
            #     '%s %d %s',
            #     caller.f_code.co_filename, caller.f_lineno, caller.f_code.co_name
            # )

            logger.debug("Model {} {}'s value is None, try to get detail."
                         .format(repr(self), name))
            obj = cls.get(self.identifier)
            if obj is not None:
                for field in cls.meta.fields:
                    # 类似 @property/@cached_field 等字段，都应该加入到
                    # fields_no_get 列表中
                    if field in cls.meta.fields_no_get:
                        continue
                    # 这里不能使用 getattr，否则有可能会无限 get
                    fv = object.__getattribute__(obj, field)
                    if fv is not None:
                        setattr(self, field, fv)
                self.stage = ModelStage.gotten
                self.exists = ModelExistence.yes
            else:
                self.exists = ModelExistence.no
                logger.warning('Model {} get return None'.format(cls_name))
            value = object.__getattribute__(self, name)
        return value

    @classmethod
    def create_by_display(cls, identifier, **kwargs):
        """create model instance with identifier and display fields"""
        model = cls(identifier=identifier)
        model.stage = ModelStage.display
        model.exists = ModelExistence.unknown
        for k, v in kwargs.items():
            if k in cls.meta.fields_display:
                setattr(model, k + '_display', v)
        return model
