import asyncio
from typing import Protocol

from .data_structure import SessionOptions


class SessionLike(Protocol):
    options: SessionOptions

    @property
    def writer(self) -> asyncio.StreamWriter:
        ...
