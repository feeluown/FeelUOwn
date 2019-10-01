class FuoException(Exception):
    pass


class ReaderException(FuoException):
    pass


class ReadFailed(ReaderException):
    pass
