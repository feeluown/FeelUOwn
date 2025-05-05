"""
Model v2 design principles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. as much compatible as possible
2. as less magic as possible

Thinking in Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Q: Object or dict to store data?
A: Object is more fiendly with lint/code-auto-completion, so we have `Models`.

Q: What data/attributes should a `Model` (not) have (use *Song* as the example)?
A:
 1. identifier/title/album_name/...    -> yes: they never change
 2. url                                -> no: it changes too fast
 3. web_url                            -> no: it can be cooked with metadata
 4. album_id/artist_id                 -> yes: all providers supports these fields
 5. mv_id/comments_id/...              -> no: only some providers supports these fields

Q: One or two or many Model for one kind of object (use *Song* as the example)?
A: Obviously, we should not have too many `Model` for one Song. One `Model` is
 not so convenient. Two **seems** to be the best option. A Brief{X}Model for
 minimum and a {X}Model for some details. Extra details can be visited by
 library.{X}_{y} method.

 Q-sub1: What attributes should a Brief{X}Model have?
 A: There are several judging rules
  1. A *human* MUST be able to identify which X it is when he saw all these attributes.
  2. Each model instance must have an unique identifier to distinguish from each other.
     The provider SHOULD identify which X it is when it knows the model type and
     the indentifier.
  3. All attributes are RECOMMENDED to be string type.
  4. Less attributes as possible when the upper rules are satisfied.

 Q-sub2: What attributes should a {X}Model have?
 A: There are several judging rules
  1. Refer to some existing spec. For example, for Song model, there is already
     an ID3 tag spec. Almost all those fields defined in ID3 tag CAN be added to
     SongModel.
  2. Refer to the provider server API spec. Usually, a provider have {x}_detail API
     for a instance, and the {X}Model is RECOMMENDED to have the same attributes.
  3. Generally, a {X}Model instance can be intialized by access one or two IO operations.
     If too many operations are needed, the design CAN be bad.

 Q-sub3: Rules for adding attributes to a {X}Model?
 A:
  1. MUST keep backward compatibility, which means all new attributes should be optional
     or they have default values.
  2. Non-string type attributes are not RECOMMENDED to add.
"""

import time
from typing import List, Optional, Tuple, Any, Union

from pydantic import (
    ConfigDict, BaseModel as _BaseModel, PrivateAttr,
    model_validator, model_serializer, Field,
)

try:
    # pydantic>=2.0
    from pydantic import field_validator
    identifier_validator = field_validator('identifier', mode='before')
    pydantic_version = 2
except ImportError:
    # pydantic<2.0
    from pydantic import validator
    identifier_validator = validator('identifier', pre=True)  # type: ignore
    pydantic_version = 1

from feeluown.utils.utils import elfhash
from .base import ModelType, ModelFlags, AlbumType, MediaFlags
from .base import SearchType  # noqa
from .model_state import ModelState


TSong = Union['SongModel', 'BriefSongModel']
TAlbum = Union['AlbumModel', 'BriefAlbumModel']
TArtist = Union['ArtistModel', 'BriefArtistModel']
TVideo = Union['VideoModel', 'BriefVideoModel']
TPlaylist = Union['PlaylistModel', 'BriefPlaylistModel']
TUser = Union['UserModel', 'BriefUserModel']


def fmt_artists_names(names: List[str]) -> str:
    """Format artists names.

    >>> fmt_artists_names(['a', 'b', 'c'])
    'a, b & c'
    >>> fmt_artists_names(['a'])
    'a'
    """
    length = len(names)
    if length == 0:
        return ''
    elif length == 1:
        return names[0]
    else:
        return ' & '.join([', '.join(names[:-1]), names[-1]])


def fmt_artists(artists: List['BriefArtistModel']) -> str:
    return fmt_artists_names([artist.name for artist in artists])


def get_duration_ms(duration):
    if duration is not None:
        seconds = duration / 1000
        m, s = seconds / 60, seconds % 60
    else:
        m, s = 0, 0
    return '{:02}:{:02}'.format(int(m), int(s))


# When a model is fully supported (with v2 design), it means
# the library has implemented all features(functions) for this model.
# You can do anything with model v2 without model v1.
#
# Also, the corresponding v1 model is deprecated.
V2SupportedModelTypes = (ModelType.song, ModelType.album, ModelType.video,
                         ModelType.artist, ModelType.playlist)


class ModelMeta:
    def __init__(self, flags, model_type):
        self.flags = flags
        self.model_type = model_type

    @classmethod
    def create(cls, model_type=ModelType.dummy, is_brief=False, is_normal=False):
        flags = ModelFlags.v2
        assert not (is_brief is is_normal is True)
        if is_brief is True:
            flags |= ModelFlags.brief
        if is_normal is True:
            flags |= ModelFlags.normal
        return cls(model_type=model_type, flags=flags)


class BaseModel(_BaseModel):
    # Do not use Model.from_orm to convert v1 model to v2 model
    # since v1 model has too much magic.
    #
    # Forbidding extra fields is good for debugging. The default behavior
    # is a little implicit. If you want to store an extra attribute on model,
    # use :meth:`cache_set` explicitly.

    # For pydantic v2.
    if pydantic_version == 2:
        model_config = ConfigDict(from_attributes=False,
                                  extra='forbid',
                                  use_enum_values=True)
    else:
        # For pydantic v1.
        class Config:
            # Do not use Model.from_orm to convert v1 model to v2 model
            # since v1 model has too much magic.
            orm_mode = False
            # Forbidding extra fields is good for debugging. The default behavior
            # is a little implicit. If you want to store an extra attribute on model,
            # use :meth:`cache_set` explicitly.
            extra = 'forbid'

    _cache: dict = PrivateAttr(default_factory=dict)
    meta: Any = ModelMeta.create()

    identifier: str
    # Before, the default value of source is 'dummy', which is too implicit.
    source: str = 'dummy'
    state: ModelState = ModelState.artificial

    @identifier_validator
    def int_to_str(cls, v):
        # Old version pydantic convert int to str implicitly.
        # Many plugins(such as netease) use int as indentifier during initialization.
        # To keep backward compatibility, convert int to str here.
        if isinstance(v, int):
            return str(v)
        return v

    def cache_get(self, key) -> Tuple[Any, bool]:
        if key in self._cache:
            value, expired_at = self._cache[key]
            if expired_at is None or expired_at >= int(time.time()):
                return value, True
        return None, False

    def cache_set(self, key, value, ttl=None):
        """
        :param int ttl: the unit is seconds.
        """
        if ttl is None:
            expired_at = None
        else:
            expired_at = int(time.time()) + ttl
        self._cache[key] = (value, expired_at)

    """
    Implement __hash__ and __eq__ so that a model can be a dict key.
    From the benchmark result, the cost of __hash__ is almost equal to __eq__.
    """
    def __hash__(self):
        id_hash = elfhash(f'{self.source}{self.identifier}'.encode())
        return id_hash * 1000 + id(type(self)) % 1000

    def __eq__(self, other):
        """Implement __hash__ and __eq__ so that model can be a dict key"""
        if not isinstance(other, BaseModel):
            return False
        return all([other.source == self.source,
                    str(other.identifier) == str(self.identifier),
                    ModelType(other.meta.model_type) == self.meta.model_type])

    def __getattr__(self, attr):
        try:
            return super().__getattr__(attr)
        except AttributeError:
            if attr.endswith('_display'):
                return getattr(self, attr[:-8])
            raise

    @model_validator(mode='before')
    def _deserialize(cls, value):
        if isinstance(value, dict):
            js = value
            if 'provider' in js:
                js['source'] = js.pop('provider', None)
            js.pop('uri', None)
            js.pop('__type__', None)
            return js
        return value

    @model_serializer(mode='wrap')
    def _serialize(self, f):
        from feeluown.library import reverse

        js = f(self)
        # FIXME: pydantic >=2.11 has a bug that it may call this method
        # multiple times -> https://github.com/pydantic/pydantic/issues/11505
        # So the `js` may not have `meta` and `state` field sometimes.
        # What's even more buggy is that it does not raise exception when
        # `js` does not have `meta` and `state`.
        #
        # For example, SongModel has a field album with TAlbum type,
        # pydantic may try to serialize the model with BriefAlbumModel even
        # if the model is actually AlbumModel.
        #
        # Without this workaround, the test case `test_serialize_model`
        # will fail with pydantic >=2.11. See
        # https://github.com/feeluown/FeelUOwn/pull/922 for more details.
        js.pop('meta', None)
        js.pop('state', None)
        js['provider'] = js['source']
        js['uri'] = reverse(self)
        js['__type__'] = f'feeluown.library.{self.__class__.__name__}'
        return js


class BaseBriefModel(BaseModel):
    """
    BaseBriefModel -> model display stage
    Model -> model gotten stage
    """
    meta: Any = ModelMeta.create(is_brief=True)


class BaseNormalModel(BaseModel):
    meta: Any = ModelMeta.create(is_normal=False)
    state: ModelState = ModelState.upgraded


class BriefSongModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.song, is_brief=True)
    title: str = ''
    # TODO: maybe there should be a field `artist_names`
    # which return a list of artist name.
    artists_name: str = ''
    album_name: str = ''
    duration_ms: str = ''

    def __str__(self):
        return f'{self.source}:{self.title}•{self.artists_name}'


class BriefVideoModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.video, is_brief=True)
    title: str = ''
    artists_name: str = ''
    duration_ms: str = ''


class BriefAlbumModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.album, is_brief=True)
    name: str = ''
    artists_name: str = ''


class BriefArtistModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.artist, is_brief=True)
    name: str = ''


class BriefPlaylistModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.playlist, is_brief=True)
    name: str = ''
    creator_name: str = ''


class BriefUserModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.user, is_brief=True)
    name: str = ''


class SongModel(BriefSongModel, BaseNormalModel):
    """
    ..versionadded: 3.8.11
        The `pic_url` field.
    """
    meta: Any = ModelMeta.create(ModelType.song, is_normal=True)
    title: str
    album: Optional[TAlbum] = None
    artists: List[TArtist]
    duration: int  # milliseconds
    # A playlist can consist of multiple songs and a song can have many children.
    # The differences between playlist's songs and song' children is that
    # a child of a song usually have no album and artists. They share some
    # metadata with the parent song.
    children: List['TSong'] = []

    genre: str = ''
    date: str = ''  # For example: 2020-12-11 00:00:00, 2020-12-11T00:00:00Z
    track: str = '1/1'  # The number of the track on the album.
    disc: str = '1/1'
    # Before the field pic_url is added, user needs to fetch a AlbumModel
    # to get the image url of the song, which means that there needs another
    # IO request. However, for almost every music providers, the pic url of the song
    # can be fetched in get_song_detail API. So one IO request can be saved
    # to fetch a image url of the song.
    pic_url: str = ''
    media_flags: MediaFlags = MediaFlags.not_sure

    def model_post_init(self, _):
        super().model_post_init(_)
        self.artists_name = fmt_artists(self.artists)
        self.album_name = self.album.name if self.album else ''
        self.duration_ms = get_duration_ms(self.duration)

    def __str__(self):
        return f'{self.source}:{self.title}•{self.artists_name}'


class UserModel(BriefUserModel, BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.user, is_normal=True)
    name: str = ''
    avatar_url: str = ''


class BriefCommentModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.comment, is_brief=True)
    user_name: str = ''
    content: str = ''


class CommentModel(BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.comment, is_normal=True)
    user: BriefUserModel
    content: str
    #: -1 means that the provider does not have such data
    liked_count: int
    #: unix timestamp, for example 1591695620
    time: int
    #: the parent comment which this comment replies to
    parent: Optional[BriefCommentModel] = None
    #: the root comment id
    root_comment_id: Optional[str] = None


class ArtistModel(BriefArtistModel, BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.artist, is_normal=True)
    name: str
    pic_url: str
    aliases: List[str]
    hot_songs: List[BriefSongModel]
    description: str
    song_count: int = -1
    album_count: int = -1
    mv_count: int = -1


class AlbumModel(BriefAlbumModel, BaseNormalModel):
    """
    .. versionadded:: 3.8.12
        The `song_count` field.
    """
    meta: Any = ModelMeta.create(ModelType.album, is_normal=True)
    name: str
    cover: str
    type_: AlbumType = Field(default=AlbumType.standard, validate_default=True)
    artists: List[BriefArtistModel]
    # One album usually has limited songs, and many providers' album_detail API
    # can return songs list. UPDATE(3.8.12): However, we found that albums
    # return by list_artist_album API usually has all fields except songs field.
    # To solve this problem, we add a song_count field to AlbumModel.
    #
    # The song_count field should be checked first, -1 means that the count is
    # unknown. The album may has songs or not. 0 means that the album has no songs.
    # And a positive number means that the album has exact number of songs.
    # If it is unknown, the songs field shuold be checked. If it is not empty,
    # just use it (to keep backward compatibility). If it is empty,
    # check if the provider supports SupportAlbumSongsReader protocol.
    songs: List[SongModel]
    song_count: int = -1
    description: str
    released: str = ''  # format: 2000-12-27.

    def model_post_init(self, _):
        super().model_post_init(_)
        self.artists_name = fmt_artists(self.artists)


class LyricModel(BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.lyric, is_normal=True)
    content: str
    trans_content: str = ''


class VideoModel(BriefVideoModel, BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.video, is_normal=True)
    title: str
    artists: List[BriefArtistModel]
    duration: int
    cover: str
    play_count: int = -1  # -1 means unknown
    released: str = ''  # publish date. format: 2000-12-27

    def model_post_init(self, _):
        super().model_post_init(_)
        self.artists_name = fmt_artists(self.artists)
        self.duration_ms = get_duration_ms(self.duration)


class PlaylistModel(BriefPlaylistModel, BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.playlist, is_normal=True)
    # Since modelv1 playlist does not have creator field, it is set to optional.
    creator: Optional[BriefUserModel] = None
    name: str
    cover: str
    description: str
    play_count: int = -1  # -1 means unknown
    created: str = ''  # format: 2000-12-27
    updated: str = ''  # format: 2000-12-27

    def model_post_init(self, _):
        super().model_post_init(_)
        if self.creator is not None:
            self.creator_name = self.creator.name


class SimpleSearchResult(_BaseModel):
    q: str
    songs: List[TSong] = []
    albums: List[TAlbum] = []
    artists: List[TArtist] = []
    playlists: List[TPlaylist] = []
    videos: List[TVideo] = []
    source: str = ''
    err_msg: str = ''


_type_modelcls_mapping = {
    ModelType.song: (SongModel, BriefSongModel),
    ModelType.album: (AlbumModel, BriefAlbumModel),
    ModelType.artist: (ArtistModel, BriefArtistModel),
    ModelType.video: (VideoModel, BriefVideoModel),
    ModelType.playlist: (PlaylistModel, BriefPlaylistModel),
    ModelType.user: (UserModel, BriefUserModel),
}


def get_modelcls_by_type(model_type: ModelType, brief=False):
    # return None when there is no brief model for them.
    # THINKING: maybe LyricModel and CommentModel will never has
    # a corresponding brief model.
    if model_type in _type_modelcls_mapping:
        modelcls, brief_modelcls = _type_modelcls_mapping[model_type]
        if brief:
            return brief_modelcls
        return modelcls
    return None
