from typing import Tuple, List, Optional, cast

from feeluown.media import Media, Quality
from feeluown.models import ModelType
from .models import CommentModel
from .model_protocol import SongProtocol, LyricProtocol, VideoProtocol
from .flags import Flags
from .excs import MediaNotFound, ModelNotFound, NoUserLoggedIn, \
    NotSupported  # noqa


def check_flags(provider, model_type: ModelType, flags: Flags):
    """

    Example::

        {
           ModelType.song: [Flags.get],
           None: [Flags.current_user]  # flags that is not related to any model
        }
    """
    return provider.meta.flags.get(model_type, Flags.none) & flags


class ProviderV2:
    class meta:
        identifier: str = ''
        name: str = ''
        flags: dict = {}

    check_flags = check_flags

    def model_get(self, model_type, model_id):
        if model_type == ModelType.song:
            return self.song_get(model_id)
        elif model_type == ModelType.video:
            return self.video_get(model_id)
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

    def has_current_user(self) -> bool:
        """Check if there is a logged in user."""

    def get_current_user(self):
        """Get current logged in user

        :raises NoUserLoggedIn: there is no logged in user.
        """

    """methods for different models
    """
    def song_get(self, identifier) -> SongProtocol:
        """
        :raises ModelNotFound: identifier is invalid
        """

    def song_list_similar(self, song):
        """List similar songs

        flag: (ModelType.song, Flags.similar_song)
        """

    def song_get_media(self, song, quality) -> Optional[Media]:
        """
        :return: when quality is not valid, return None
        """

    def song_list_quality(self, song) -> List[Quality.Audio]:
        """
        """
        raise NotImplementedError

    def song_select_media(self, song, policy=None) -> Tuple[Media, Quality.Audio]:
        """
        :raises: MediaNotFound
        """
        media, quality = self._select_media(song, policy)
        assert isinstance(quality, Quality.Audio)
        return media, quality

    def song_list_hot_comments(self, song) -> List[CommentModel]:
        """
        """

    def song_get_web_url(self, song) -> str:
        pass

    def song_get_lyric(self, song) -> Optional[LyricProtocol]:
        """
        Provider has Flags.lyric must implemente this interface.
        """

    def song_get_mv(self, song) -> Optional[VideoProtocol]:
        """
        Provider has Flags.mv must implement this interface.
        """

    def video_get(self, identifier) -> VideoProtocol:
        """
        :raises ModelNotFound: identifier is invalid
        """

    def video_get_media(self, video, quality) -> Optional[Media]:
        """
        Provider has Flags.multi_quality must implemente this interface.

        :return: when quality is not valid, return None
        """

    def video_list_quality(self, video) -> List[Quality.Video]:
        """
        Provider has Flags.multi_quality must implemente this interface.
        """

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
