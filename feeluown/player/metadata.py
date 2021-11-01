from collections.abc import MutableMapping
from enum import Enum


class MetadataFields(Enum):
    """
    Check the following docs for fields definition
    0. id3tag
    1. www.freedesktop.org -> mpris-spec/metadata/#fields
    2. developer.apple.com -> MPMediaItem
    """
    # setby refers to how the metadata is generated/gotten.
    setby = '__setby__'

    title = 'title'
    artists = 'artists'  # The value is a list of strings.
    album = 'album'
    year = 'year'
    genre = 'genre'
    track = 'track'  # The track number on the album disc.
    source = 'source'


class Metadata(MutableMapping):
    """Metadata is a dict that transform the key to MetadataFields.
    """
    def __init__(self, *args, **kwargs):
        self._store = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, name):
        return self._store[self._to_field(name)]

    def __contains__(self, name):
        return self._to_field(name) in self._store

    def __setitem__(self, key, value):
        self._store[self._to_field(key)] = value

    def __delitem__(self, key):
        del self._store[self._to_field(key)]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def _to_field(self, name):
        try:
            field = MetadataFields(name)
        except ValueError:
            raise KeyError(f'invalid key {name}') from None
        else:
            return field
