# -*- coding: utf-8 -*-

"""
feeluown.library
~~~~~~~~~~~~~~~~

"""
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Tuple, cast

from feeluown.media import Media, Quality
from .base import ModelType
from .models import V2SupportedModelTypes
from .flags import Flags
from .excs import MediaNotFound, ModelNotFound, NoUserLoggedIn  # noqa


class AbstractProvider(ABC):
    """
    For backward compatibility. Many providers use this as base class.
    """


class Provider:
    class meta:
        identifier: str = ''
        name: str = ''
        flags: dict = {}

    def __init__(self):
        self._user = None

    @property
    @abstractmethod
    def identifier(self):
        """provider identify"""

    @property
    @abstractmethod
    def name(self):
        """provider name"""

    def __str__(self):
        return f'provider:{self.identifier}'

    @contextmanager
    def auth_as(self, user):
        """auth as a user temporarily

        Usage::

            with auth_as(user):
                ...
        """
        old_user = self._user
        self.auth(user)
        try:
            yield
        finally:
            self.auth(old_user)

    def auth(self, user):
        """use provider as a specific user"""
        self._user = user

    def get_current_user_or_none(self):
        """
        .. versionadded: 4.0
        """
        try:
            return self.get_current_user()
        except NoUserLoggedIn:
            return None

    def search(self, *args, **kwargs):
        pass

    def use_model_v2(self, model_type: ModelType) -> bool:
        """Check whether model v2 is used for the specified model_type."""
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
        raise ModelNotFound(reason=ModelNotFound.Reason.not_supported)

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


ProviderV2 = Provider
