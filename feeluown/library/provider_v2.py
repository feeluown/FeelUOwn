from typing import Tuple, cast

from feeluown.media import Media, Quality
from feeluown.models import ModelType
from .models import V2SupportedModelTypes
from .flags import Flags
from .excs import MediaNotFound, ModelNotFound, NoUserLoggedIn, \
    NotSupported  # noqa
from .provider_protocol import check_flag as check_flag_by_protocol


def check_flags(provider, model_type: ModelType, flags: Flags):
    """

    Example::

        {
           ModelType.song: [Flags.get],
           None: [Flags.current_user]  # flags that is not related to any model
        }
    """
    # TODO: also check other types with protocol.
    if model_type is ModelType.song and flags is not Flags.model_v2:
        return check_flag_by_protocol(provider, model_type, flags)
    return provider.meta.flags.get(model_type, Flags.none) & flags


class ProviderV2:
    """Base class for provider v2"""

    class meta:
        identifier: str = ''
        name: str = ''
        flags: dict = {}

    check_flags = check_flags

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
