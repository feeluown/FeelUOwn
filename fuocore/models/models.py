import logging
import warnings

from fuocore.media import MultiQualityMixin, Quality
from fuocore.utils import elfhash
from .base import ModelType, ModelStage, ModelExistence, \
    AlbumType, Model

logger = logging.getLogger(__name__)


def _get_artists_name(artists):
    # [a, b, c] -> 'a, b & c'
    artists_name = ', '.join((artist.name for artist in artists))
    return ' & '.join(artists_name.rsplit(', ', 1))


class BaseModel(Model):
    """Base model for music resource"""

    class Meta:
        """Model metadata"""

        allow_get = True  #: whether model has a valid get method
        allow_list = False  #: whether model has a valid list method
        model_type = ModelType.dummy.value

        #: declare model fields, each model must have an identifier field
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

    @classmethod
    def get(cls, identifier):
        """get model instance by identifier"""

    @classmethod
    def list(cls, identifier_list):
        """Model batch get method"""


class ArtistModel(BaseModel):
    """Artist Model"""

    class Meta:
        model_type = ModelType.artist.value
        fields = ['name', 'cover', 'songs', 'desc', 'albums']
        fields_display = ['name']
        allow_create_songs_g = False
        allow_create_albums_g = False

    def __str__(self):
        return 'fuo://{}/artists/{}'.format(self.source, self.identifier)

    def create_songs_g(self):
        """create songs generator(alpha)"""
        pass

    def create_albums_g(self):
        pass

    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if name == 'songs':
            warnings.warn('please use/implement .create_songs_g')
        return value


class AlbumModel(BaseModel):
    class Meta:
        model_type = ModelType.album.value

        # TODO: 之后可能需要给 Album 多加一个字段用来分开表示 artist 和 singer
        # 从意思上来区分的话：artist 是专辑制作人，singer 是演唱者
        # 像虾米音乐中，它即提供了专辑制作人信息，也提供了 singer 信息
        fields = ['name', 'cover', 'songs', 'artists', 'desc', 'type']
        fields_display = ['name', 'artists_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if kwargs.get('type') is None:
            name = kwargs.get('name')
            if name:
                self.type = AlbumType.guess_by_name(name)
            else:
                self.type = AlbumType.standard

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


class MvModel(BaseModel, MultiQualityMixin):
    QualityCls = Quality.Video

    class Meta:
        fields = ['name', 'media', 'desc', 'cover', 'artist']
        support_multi_quality = False


class SongModel(BaseModel, MultiQualityMixin):
    QualityCls = Quality.Audio

    class Meta:
        model_type = ModelType.song.value
        fields = ['album', 'artists', 'lyric', 'comments', 'title', 'url',
                  'duration', 'mv', 'media']
        fields_display = ['title', 'artists_name', 'album_name', 'duration_ms']

        support_multi_quality = False

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
        else:
            m, s = 0, 0
        return '{:02}:{:02}'.format(int(m), int(s))

    @property
    def filename(self):
        return '{} - {}.mp3'.format(self.title, self.artists_name)

    def __str__(self):
        return 'fuo://{}/songs/{}'.format(self.source, self.identifier)  # noqa

    def __hash__(self):
        try:
            id_hash = int(self.identifier)
        except ValueError:
            id_hash = elfhash(self.identifier.encode())
        return id_hash * 1000 + id(type(self)) % 1000

    def __eq__(self, other):
        if not isinstance(other, SongModel):
            return False
        return all([other.source == self.source,
                    other.identifier == self.identifier])


class PlaylistModel(BaseModel):
    class Meta:
        model_type = ModelType.playlist.value
        fields = ['name', 'cover', 'songs', 'desc']
        fields_display = ['name']
        allow_create_songs_g = False

    def __str__(self):
        return 'fuo://{}/playlists/{}'.format(self.source, self.identifier)

    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if name == 'songs':
            warnings.warn('please use/implement .create_songs_g')
        return value

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

    TODO: support album and artist
    """
    class Meta:
        model_type = ModelType.dummy.value

        # XXX: songs should be a empty list instead of None
        # when there is not song.
        fields = ['q', 'songs', 'playlists', 'artists', 'albums']
        fields_no_get = ['q', 'songs', 'playlists', 'artists', 'albums']

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
                  'fav_albums', 'fav_artists', 'rec_songs', 'rec_playlists']
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

    def add_to_fav_artists(self, aritst_id):
        pass

    def remove_from_fav_artists(self, artist_id):
        pass
