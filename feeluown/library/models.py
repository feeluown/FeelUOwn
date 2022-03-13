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
from typing import List, Optional, Tuple, Any

from pydantic import BaseModel as _BaseModel, PrivateAttr

from feeluown.models import ModelType, ModelExistence, ModelStage, ModelFlags, AlbumType
from feeluown.utils.utils import elfhash
from .model_state import ModelState


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
    class Config:
        # Do not use Model.from_orm to convert v1 model to v2 model
        # since v1 model has too much magic.
        orm_mode = False
        # Forbidding extra fields is good for debugging. The default behavior
        # is a little implicit. If you want to store an extra attribute on model,
        # use :meth:`cache_set` explicitly.
        extra = 'forbid'

    __cache__: dict = PrivateAttr(default_factory=dict)
    meta: Any = ModelMeta.create()

    identifier: str
    # Before, the default value of source is 'dummy', which is too implicit.
    source: str = 'dummy'
    state: ModelState = ModelState.artificial

    #: (DEPRECATED) for backward compact
    exists: ModelExistence = ModelExistence.unknown

    def cache_get(self, key) -> Tuple[Any, bool]:
        if key in self.__cache__:
            value, expired_at = self.__cache__[key]
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
        self.__cache__[key] = (value, expired_at)

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
            return super().__getattribute__(attr)
        except AttributeError:
            if attr.endswith('_display'):
                return getattr(self, attr[:-8])
            raise


class BaseBriefModel(BaseModel):
    """
    BaseBriefModel -> model display stage
    Model -> model gotten stage
    """
    meta: Any = ModelMeta.create(is_brief=True)

    @classmethod
    def from_display_model(cls, model):
        """Create a new model from an old model in display stage.

        This method never triggers IO operations.
        """
        # Due to the display_property mechanism, it is unsafe to
        # get attribute of other stage model property.
        assert model.stage is ModelStage.display
        data = {'state': cls._guess_state_from_exists(model.exists)}
        for field in cls.__fields__:
            if field in ('state', 'meta'):
                continue
            if field in ('identifier', 'source', 'exists'):
                value = object.__getattribute__(model, field)
            else:
                if field in model.meta.fields_display:
                    value = getattr(model, f'{field}_display')
                else:
                    # For example, BriefVideoModel has field `artists_name` and
                    # the old model does not have such display field.
                    value = ''
            data[field] = value
        return cls(**data)

    @classmethod
    def _guess_state_from_exists(cls, exists):
        if exists == ModelExistence.no:
            state_value = ModelState.not_exists
        elif exists == ModelExistence.unknown:
            state_value = ModelState.artificial
        else:
            state_value = ModelState.exists
        return state_value


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


class SongModel(BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.song, is_normal=True)
    title: str
    album: Optional[BriefAlbumModel]
    artists: List[BriefArtistModel]
    duration: int  # milliseconds

    @property
    def artists_name(self):
        return fmt_artists(self.artists)

    @property
    def album_name(self):
        return self.album.name if self.album else ''

    @property
    def duration_ms(self):
        if self.duration is not None:
            seconds = self.duration / 1000
            m, s = seconds / 60, seconds % 60
        else:
            m, s = 0, 0
        return '{:02}:{:02}'.format(int(m), int(s))


class UserModel(BaseNormalModel):
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
    parent: Optional[BriefCommentModel]
    #: the root comment id
    root_comment_id: Optional[str]


class ArtistModel(BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.artist, is_normal=True)
    name: str
    pic_url: str
    aliases: List[str]
    hot_songs: List[SongModel]
    description: str


class AlbumModel(BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.album, is_normal=True)
    name: str
    cover: str
    type_: AlbumType = AlbumType.standard
    artists: List[BriefArtistModel]
    # One album usually has limited songs, and many providers' album_detail API
    # can return songs list.
    songs: List[SongModel]
    description: str

    @property
    def artists_name(self):
        return fmt_artists(self.artists)


class LyricModel(BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.lyric, is_normal=True)
    content: str
    trans_content: str = ''


class VideoModel(BaseNormalModel):
    meta: Any = ModelMeta.create(ModelType.video, is_normal=True)
    title: str
    artists: List[BriefArtistModel]
    duration: int
    cover: str

    @property
    def artists_name(self):
        return fmt_artists(self.artists)

    @property
    def duration_ms(self):
        if self.duration is not None:
            seconds = self.duration / 1000
            m, s = seconds / 60, seconds % 60
        else:
            m, s = 0, 0
        return '{:02}:{:02}'.format(int(m), int(s))


class PlaylistModel(BaseBriefModel):
    meta: Any = ModelMeta.create(ModelType.playlist, is_normal=True)
    # Since modelv1 playlist does not have creator field, it is set to optional.
    creator: Optional[BriefUserModel]
    name: str
    cover: str
    description: str


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
