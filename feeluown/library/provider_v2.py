from typing import Tuple, cast

from feeluown.media import Media, Quality
from .base import ModelType
from .models import V2SupportedModelTypes
from .flags import Flags
from .excs import MediaNotFound, ModelNotFound, NoUserLoggedIn, \
    NotSupported  # noqa


class ProviderV2:
    """Base class for provider v2"""

    class meta:
        identifier: str = ''
        name: str = ''

        #: deprecated: use provider protocol instead.
        flags: dict = {}

    def use_model_v2(self, model_type: ModelType) -> bool:
        """Check whether model v2 is used for the specified model_type.

        For feeluown developer, there are three things you should know.

        1. Both v2 model and v1 model implement BriefXProtocol, which means
           model.{attirbute}_display works for both models. For exmample,
           SongModel(v2), BriefSongModel(v2) and SongModel(v1) all implement
           BriefSongProtocol. So no matter which version the `song` is, it is
           always safe to access `song.title_display`.

        2. When model v2 is used, it means the way of accessing model's attributes
           becomes different. So you should always check which version
           the model is before accessing some attributes.

           For model v1, you can access all model's attributes by {model}.{attribute},
           and IO(network) operations may be performed implicitly. For example,
           the code `song.url` *may* trigger a network request to fetch the
           url when `song.url` is currently None. Tips: you can check the
           `BaseModel.__getattribute__` implementation in `feeluown.library` package
           for more details.

           For model v2, everything are explicit. Basic attributes of model can be
           accessed by {model}.{attribute} and there will be no IO operations.
           Other attributes can only be accessed with methods of library. For example,
           you can access song url/media info by `library.song_prepare_media`.

        3. When deserializing model from a text line, the model version is important.
           If provider does not declare it uses model v2, feeluown just use model v1
           to do deserialization to keep backward compatibility.
        """
        return Flags.model_v2 in self.meta.flags.get(model_type, Flags.none)

    def model_get(self, model_type, model_id):
        if model_type in V2SupportedModelTypes:
            if model_type == ModelType.song:
                return self.song_get(model_id)
            elif model_type == ModelType.video:
                return self.video_get(model_id)
            elif model_type == ModelType.album:
                return self.album_get(model_id)
            elif model_type == ModelType.artist:
                return self.artist_get(model_id)
            elif model_type == ModelType.playlist:
                return self.playlist_get(model_id)
        raise NotSupported

    def _model_cache_get_or_fetch(self, model, cache_key):
        """Util method for getting value of cached field

        .. versionadded: 3.7.12
        """
        value, exists = model.cache_get(cache_key)
        if not exists:
            upgrade_model = self.model_get(model.meta.model_type, model.identifier)
            value, exists = upgrade_model.cache_get(cache_key)
            assert exists is True
            model.cache_set(cache_key, value)
        return value

    def song_select_media(self, song, policy=None) -> Tuple[Media, Quality.Audio]:
        """
        :raises: MediaNotFound
        """
        media, quality = self._select_media(song, policy)
        assert isinstance(quality, Quality.Audio)
        return media, quality

    def video_select_media(self, video, policy=None) -> Tuple[Media, Quality.Video]:
        """
        :raises: MediaNotFound
        """
        media, quality = self._select_media(video, policy)
        assert isinstance(quality, Quality.Video)
        return media, quality

    def _select_media(self, playable_model, policy=None):
        if ModelType(playable_model.meta.model_type) is ModelType.song:
            list_quality = self.song_list_quality
            QualityCls = Quality.Audio
            get_media = self.song_get_media
            policy = 'hq<>' if policy is None else policy
        else:
            list_quality = self.video_list_quality
            QualityCls = Quality.Video
            get_media = self.video_get_media
            policy = 'hd<>' if policy is None else policy

        # fetch available quality list
        available_q_set = set(list_quality(playable_model))
        if not available_q_set:
            raise MediaNotFound

        sorted_q_list = Quality.SortPolicy.apply(
            policy, [each.value for each in list(QualityCls)])

        # find the first available quality
        for quality in sorted_q_list:
            quality = QualityCls(quality)
            if quality not in available_q_set:
                continue
            media = get_media(playable_model, quality)
            if media is not None:
                media = cast(Media, media)
            else:
                # Media is not found for the quality. The provider show
                # a non-existing quality.
                raise MediaNotFound(
                    f'provider:{playable_model.source} has nonstandard implementation')
            return media, quality
        assert False, 'this should not happen'
