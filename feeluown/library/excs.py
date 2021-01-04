class LibraryException(Exception):
    pass


class NotSupported(LibraryException):
    pass


class MediaNotFound(LibraryException):
    pass
