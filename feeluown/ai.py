from typing import TYPE_CHECKING

from openai import AsyncOpenAI

if TYPE_CHECKING:
    from feeluown.library import BriefSongModel


class AI:
    def __init__(self, base_url, api_key, model):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

    def get_async_client(self):
        return AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
