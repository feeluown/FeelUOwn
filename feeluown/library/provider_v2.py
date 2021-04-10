from typing import Tuple, List

from feeluown.media import Media, Quality
from feeluown.models import ModelType
from .models import CommentModel
from .model_protocol import SongProtocol
from .flags import Flags
from .excs import MediaNotFound, ModelNotFound, NoUserLoggedIn  # noqa


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

    def has_current_user(self) -> bool:
        """Check if there is a logged in user."""

    def get_current_user(self):
        """Get current logged in user

        :raises NoUserLoggedIn: there is no logged in user.
        """

    def song_get(self, identifier) -> SongProtocol:
        """
        :raises ModelNotFound: identifier is invalid
        """

    def song_list_similar(self, song):
        """List similar songs

        flag: (ModelType.song, Flags.similar_song)
        """

    def song_get_media(self, song, quality):
        pass

    def song_list_quality(self, song) -> List[Quality.Audio]:
        pass

    def song_select_media(self, song, policy=None) -> Tuple[Media, Quality.Audio]:
        """
        :raises: MediaNotFound
        """
        # fetch available quality list
        available_q_set = set(self.song_list_quality(song))
        if not available_q_set:
            raise MediaNotFound

        QualityCls = Quality.Audio
        # translate policy into quality priority list
        if policy is None:
            policy = 'hq<>'
        sorted_q_list = Quality.SortPolicy.apply(
            policy, [each.value for each in list(QualityCls)])

        # find the first available quality
        for quality in sorted_q_list:
            quality = QualityCls(quality)
            if quality in available_q_set:
                return self.song_get_media(song, quality), quality

        assert False, 'this should not happen'

    def song_list_hot_comments(self, song) -> List[CommentModel]:
        pass
