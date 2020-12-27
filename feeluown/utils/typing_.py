# flake8: noqa
from typing import TYPE_CHECKING


try:
    from typing import Protocol
except ImportError:
    if not TYPE_CHECKING:
        from typing_extensions import Protocol
