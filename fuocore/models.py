# -*- coding: utf-8 -*-

"""
音乐资源模型
~~~~~~~~~~~~

这个模块定义了音乐资源的模型，如歌曲模型： ``SongModel`` , 歌手模型： ``ArtistModel`` 。
它们都类似这样::

    class XyzModel(BaseModel):
        class Meta:
            model_type = ModelType.xyz
            fields = ['identifier', 'a', 'b', 'c']

        @property
        def ab(self):
            return self.a + self.b


可以看到，XyzModel 继承于 BaseModel，并且有个 Meta 类属性。
在这个例子种，Meta 类保存了 XyzModel 的一些元信息：Xyz 模型有哪些字段(fields),
以及 Xyz 模型的类型(model_type).

.. note::

    有同学或许会觉得：在 XyzModel 类中又定义了一个 Meta 类，这不是很奇怪么？
    这个设计是借鉴 django Model Meta 设计，目的是尽量保证 XyzModel
    属性名字空间简洁干净。

创建模型实例
++++++++++++++++

我们支持两种创建模型的方法，每种方法都有其适用的场景。

**最容易想到的的创建实例的方法是通过构造函数创建** 。

以 SongModel 为例::

    song = SongModel(identifier=123, title='Love Story',
                     url='http://xxx.mp3', duration=1000.0)

可以看出，这个方法要求我们知道大部分属性的准确的值。当我们能通过网络请求（或其它方式）
获取到了一个实例的所有准确信息时，我们推荐用这个方式来实例化。举个例子，
feeluown-netease 的 NeteaseSongModel.get 方法就是通过这种方法来实例化对像的。

但有时候，我们可能只知道实例 identifier、名字两个信息，并且我们不是特别确定这个名字是否正确，
那我们就不应该使用上述方法。

这时，我们可以 **通过 create_by_display 方法来创建实例** .
这个方法一般不会用到，目前主要用于 feeluown 内部，这里不多介绍。

实例生命周期
++++++++++++++++

两种方式创建的实例所处的生命阶段是不一样的。在一个实例的生命周期中，
它有三个阶段：display, inited, gotten. 通过构造函数创建的实例所处的阶段是
inited, 通过 create_by_display 方法创建的实例所处阶段是 dispaly.

::

    -----------
    | dispaly |  ----
    -----------      \        ----------
                      ------> | gotten |
    ----------       /        ----------
    | inited |  -----
    ----------

当实例处于 display 和 inited 阶段时，它们的某些字段可能还没有被初始化，
值是 None. 这时侯，如果调用方访问了这个实例的任意一个未初始化的字段，
就会触发实例的进化：调用 Model.get 方法来获取实例所有属性的值，
用这些值来重新初始化实例，初始化完毕后实例就会进入 gotten 阶段。
详细逻辑请阅读 ``BaseModel.__getattribute__`` 源码。
"""

from enum import IntEnum
import logging


logger = logging.getLogger(__name__)


def _get_artists_name(artists):
    return ','.join((artist.name for artist in artists))


class ModelType(IntEnum):
    dummy = 0

    song = 1
    artist = 2
    album = 3
    playlist = 4
    lyric = 5

    user = 17


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
                           'fields_no_get': []}
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

        for field in fields_display:
            setattr(klass, field + '_display', display_property(field))

        # DEPRECATED attribute _meta
        # TODO: remove this in verion 2.3
        klass._meta = ModelMetadata(model_type=model_type,
                                    provider=provider,
                                    fields=fields_all,
                                    fields_display=fields_display,
                                    fields_no_get=fields_no_get,
                                    **meta_kv)
        klass.source = provider.identifier if provider is not None else None
        # use meta attribute instead of _meta
        klass.meta = klass._meta
        return klass


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
        for field in self._meta.fields:
            setattr(self, field, getattr(obj, field, None))

        for k, v in kwargs.items():
            if k in self._meta.fields:
                setattr(self, k, v)


class BaseModel(Model):
    """Base model for music resource.

    :param identifier: model object identifier, unique in each provider

    :cvar allow_get: meta var, whether model has a valid get method
    :cvar allow_list: meta var, whether model has a valid list method
    """

    class Meta:
        allow_get = True
        allow_list = False
        model_type = ModelType.dummy.value

        #: Model 所有字段，子类可以通过设置该字段以添加其它字段
        fields = ['identifier']

        #: Model 用来展示的字段
        fields_display = []

        #: 不触发 get 的 Model 字段，这些字段往往 get 是获取不到的
        fields_no_get = ['identifier']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #: model 所处阶段。目前，通过构造函数初始化的 model
        # 所处阶段为 inited，通过 get 得到的 model，所处阶段为 gotten，
        # 通过 display 属性构造的 model，所处阶段为 display。
        # 目前，此属性仅为 models 模块使用，不推荐外部依赖。
        self.stage = kwargs.get('stage', ModelStage.inited)

        #: 歌曲是否存在。如果 Model allow_get，但 get 却不能获取到 model，
        # 则该 model 不存在。
        self.exists = ModelExistence.unknown

    def __eq__(self, other):
        if not isinstance(other, BaseModel):
            return False
        return all([other.source == self.source,
                    other.identifier == self.identifier,
                    other.meta.model_type == self.meta.model_type])

    def __getattribute__(self, name):
        """
        获取 model 某一属性时，如果该属性值为 None 且该属性是 field
        且该属性允许触发 get 方法，这时，我们尝试通过获取 model
        详情来初始化这个字段，于此同时，还会重新给除 identifier
        外的所 fields 重新赋值。
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

            logger.info("Model {} {}'s value is None, try to get detail."
                        .format(repr(self), name))
            obj = cls.get(self.identifier)
            if obj is not None:
                for field in cls.meta.fields:
                    if field in ('identifier', ):
                        continue
                    # 这里不能使用 getattr，否则有可能会无限 get
                    fv = object.__getattribute__(obj, field)
                    # 如果字段属于 fields_no_get 且值为 None，则不覆盖
                    # 比如 UserModel 的 cookies 的字段，cookies
                    # 这类需要权限认证的信息往往不能在 get 时获取，
                    # 而需要在特定上下文单独设置
                    if not (fv is None and field in cls.meta.fields_no_get):
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
        model = cls(identifier=identifier)
        model.stage = ModelStage.display
        model.exists = ModelExistence.unknown
        for k, v in kwargs.items():
            if k in cls.meta.fields_display:
                setattr(model, k + '_display', v)
        return model

    @classmethod
    def get(cls, identifier):
        """获取 model 详情

        这个方法必须尽量初始化所有字段，确保它们的值不是 None。
        """

    @classmethod
    def list(cls, identifier_list):
        """Model batch get method"""


class ArtistModel(BaseModel):
    """Artist Model

    :param str name: artist name
    :param str cover: artist cover image url
    :param list songs: artist songs
    :param str desc: artist description
    """
    class Meta:
        model_type = ModelType.artist.value
        fields = ['name', 'cover', 'songs', 'desc', 'albums']
        #: alpha
        allow_create_songs_g = False

    def __str__(self):
        return 'fuo://{}/artists/{}'.format(self.source, self.identifier)

    def create_songs_g(self):
        """create songs generator(alpha)"""
        pass


class AlbumModel(BaseModel):
    """Album Model

    :param str name: album name
    :param str cover: album cover image url
    :param list songs: album songs
    :param list artists: album artists
    :param str desc: album description
    """
    class Meta:
        model_type = ModelType.album.value

        # TODO: 之后可能需要给 Album 多加一个字段用来分开表示 artist 和 singer
        # 从意思上来区分的话：artist 是专辑制作人，singer 是演唱者
        # 像虾米音乐中，它即提供了专辑制作人信息，也提供了 singer 信息
        fields = ['name', 'cover', 'songs', 'artists', 'desc']

    def __str__(self):
        return 'fuo://{}/albums/{}'.format(self.source, self.identifier)

    @property
    def artists_name(self):
        return _get_artists_name(self.artists or [])


class LyricModel(BaseModel):
    """Lyric Model

    :param SongModel song: song which lyric belongs to
    :param str content: lyric content
    :param str trans_content: translated lyric content
    """
    class Meta:
        model_type = ModelType.lyric.value
        fields = ['song', 'content', 'trans_content']


class Media:
    """视音频媒体文件或者链接

    hd/md/ld 在这里是相对概念，hd >= md >= ld。我们在构造 Media 对象的时候，
    将质量最高的标记为高清，将质量最低的媒体文件标记为低清。
    如果某个视频或者音乐只有一种质量，那么 hd/sd/ld 中应该有两个值为 None。

    :param str sq: 无损
    :param str hd: 高清
    :param str md: 标清
    :param str ld: 低清

    使用示例::

        hd, sd, ld = media
        as_high_as_possible = hd or sd or ld

    >>> list(Media.Q.better_than(Media.Q.hd))[0] == Media.Q.sq
    True
    >>> list(Media.Q.better_than(Media.Q.sq))
    []
    >>> media = Media(hd='xx', sd='yy')
    >>> media.get_url(Media.Q.hd)
    'xx'
    >>> media.get_url(Media.Q.sq)
    """
    class Q(IntEnum):  # Quality
        sq = 16
        hd = 8
        sd = 4
        ld = 2

        @classmethod
        def better_than(cls, q):
            asc = (cls.ld, cls.sd, cls.hd, cls.sq)
            for _q in asc:
                if _q > q:
                    yield _q

        @classmethod
        def worse_than(cls, q):
            desc = (cls.sq, cls.hd, cls.sd, cls.ld)
            for _q in desc:
                if _q < q:
                    yield _q

    class S(IntEnum):  # Strategy
        none = 0
        better = 1
        worse = 2

    def __init__(self, sq=None, hd=None, sd=None, ld=None):
        self.sq = sq
        self.hd = hd
        self.sd = sd
        self.ld = ld

    @property
    def url_ahap(self):
        """return url with best quality(as high as possible)"""
        return self.sq or self.hd or self.sd or self.ld

    @property
    def url_alap(self):
        """return url with worsest quality(as low as possible)"""
        return self.ld or self.sd or self.hd or self.sq

    def get_url(self, q=Q.hd, s=S.better):
        """复杂茦略"""
        mapping = {
            Media.Q.sq: self.sq,
            Media.Q.hd: self.hd,
            Media.Q.sd: self.sd,
            Media.Q.ld: self.ld
        }
        uri = mapping[q]
        if uri is not None:
            return uri
        if s == Media.S.better:
            for _q in Media.Q.better_than(q):
                if mapping[_q] is not None:
                    return mapping[_q]
        elif s == Media.s.worse:
            for _q in Media.Q.worse_than(q):
                if mapping[_q] is not None:
                    return mapping[_q]


class MvModel(BaseModel):
    """Mv Model

    :param Media media: 可播放的媒体
    """
    class Meta:
        fields = ['name', 'media', 'desc', 'cover', 'artist']


class SongModel(BaseModel):
    """Song Model

    :param str title: song title
    :param str url: song url (http url or local filepath)
    :param float duration: song duration
    :param AlbumModel album: album which song belong to
    :param list artists: song artists :class:`.ArtistModel`
    :param LyricModel lyric: song lyric
    """
    class Meta:
        model_type = ModelType.song.value
        # TODO: 支持低/中/高不同质量的音乐文件
        fields = ['album', 'artists', 'lyric', 'comments', 'title', 'url',
                  'duration', 'mv']
        fields_display = ['title', 'artists_name', 'album_name', 'duration_ms']

    @property
    def artists_name(self):
        return _get_artists_name(self.artists or [])

    @property
    def album_name(self):
        return self.album.name if self.album is not None else ''

    @property
    def duration_ms(self):
        if self.duration is not None:
            seconds = self.duration / 1000
            m, s = seconds / 60, seconds % 60
        return '{:02}:{:02}'.format(int(m), int(s))

    @property
    def filename(self):
        return '{} - {}.mp3'.format(self.title, self.artists_name)

    def __str__(self):
        return 'fuo://{}/songs/{}'.format(self.source, self.identifier)  # noqa

    def __eq__(self, other):
        if not isinstance(other, SongModel):
            return False
        return all([other.source == self.source,
                    other.identifier == self.identifier])


class PlaylistModel(BaseModel):
    """Playlist Model

    :param name: playlist name
    :param cover: playlist cover image url
    :param desc: playlist description
    :param songs: playlist songs
    """
    class Meta:
        model_type = ModelType.playlist.value
        fields = ['name', 'cover', 'songs', 'desc']
        allow_create_songs_g = False

    def __str__(self):
        return 'fuo://{}/playlists/{}'.format(self.source, self.identifier)

    def add(self, song_id):
        """add song to playlist, return true if succeed.

        If the song was in playlist already, return true.
        """
        pass

    def remove(self, song_id):
        """remove songs from playlist, return true if succeed

        If song is not in playlist, return true.
        """
        pass

    def create_songs_g(self):
        pass


class SearchModel(BaseModel):
    """Search Model

    :param q: search query string
    :param songs: songs in search result

    TODO: support album and artist
    """
    class Meta:
        model_type = ModelType.dummy.value

        # XXX: songs should be a empty list instead of None
        # when there is not song.
        fields = ['q', 'songs']

    def __str__(self):
        return 'fuo://{}?q={}'.format(self.source, self.q)


class UserModel(BaseModel):
    """User Model

    :param name: user name
    :param playlists: playlists created by user
    :param fav_playlists: playlists collected by user
    :param fav_songs: songs collected by user
    :param fav_albums: albums collected by user
    :param fav_artists: artists collected by user
    """
    class Meta:
        allow_fav_songs_add = False
        allow_fav_songs_remove = False
        allow_fav_playlists_add = False
        allow_fav_playlists_remove = False
        allow_fav_albums_add = False
        allow_fav_albums_remove = False
        allow_fav_artists_add = False
        allow_fav_artists_remove = False

        model_type = ModelType.user.value
        fields = ['name', 'playlists', 'fav_playlists', 'fav_songs',
                  'fav_albums', 'fav_artists']
        fields_display = ['name']

    def add_to_fav_songs(self, song_id):
        """add song to favorite songs, return True if success

        :param song_id: song identifier
        :return: Ture if success else False
        :rtype: boolean
        """
        pass

    def remove_from_fav_songs(self, song_id):
        pass

    def add_to_fav_playlists(self, playlist_id):
        pass

    def remove_from_fav_playlists(self, playlist_id):
        pass

    def add_to_fav_albums(self, album_id):
        pass

    def remove_from_fav_albums(self, album_id):
        pass

    def add_to_fav_artist(self, aritst_id):
        pass

    def remove_from_fav_artists(self, artist_id):
        pass
