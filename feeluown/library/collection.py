from enum import Enum
from dataclasses import dataclass
from typing import List

from .models import BaseModel


class CollectionType(Enum):
    """Collection type enumeration"""

    # These two values are only used in local collection.
    sys_library = 16
    sys_pool = 13

    only_songs = 1
    only_artists = 2
    only_albums = 3
    only_playlists = 4
    only_lyrics = 5
    only_videos = 6

    only_users = 17
    only_comments = 18

    mixed = 32


@dataclass
class Collection:
    """
    Differences between a collection and a playlist
    - A collection has no identifier in general.
    - A collection may have songs, albums and artists.
    """
    name: str
    type_: CollectionType
    models: List[BaseModel]
    description: str = ''
