"""
scanner scan a directory and build a
"""

from enum import IntEnum

KNOWN_EXTS = ('mp3', 'ogg', 'wma', 'm4a', 'm4v', 'flac')


class FileEventType(IntEnum):
    deleted = 0
    added = 1
    changed = 2


class FileEvent:
    def __init__(self, filepath, type_):
        pass


class Scanner:
    def __init__(self, paths, exts=None, depth=2):
        """

        :return: {filepath: checksum, ...}
        """
        self._exts = exts or KNOWN_EXTS
        # common directory structure are as following
        # * Music/<provider>/<artist>/<album>/<title>.<ext>
        # * Music/<provider>/<album>/<title - artist>.<ext>
        # * Music/<provider>/<title - artist>.<ext>
        # therefore, we set max depth to 3, which should be large enough
        self._depth = min(3, depth)
        self._paths = paths
