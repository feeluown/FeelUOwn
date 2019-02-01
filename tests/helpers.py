try:  # pragma: no cover
    from unittest.mock import Mock, patch, sentinel  # noqa
except ImportError:  # pragma: no cover
    from mock import Mock, patch, sentinel  # noqa

try:
    from unittest import mock  # noqa
except ImportError:
    import mock  # noqa
