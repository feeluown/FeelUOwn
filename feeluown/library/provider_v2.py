from feeluown.models import ModelType
from .flags import Flags


def check_flags(provider, model_type: ModelType, flags: Flags):
    return provider.meta.flags.get(model_type, Flags.none) & flags


class ProviderV2:
    class meta:
        identifier: str = ''
        name: str = ''
        flags: dict = {}

    check_flags = check_flags

    def song_list_similar(self, song):
        """List similar songs

        flag: (ModelType.song, Flags.similar_song)
        """
