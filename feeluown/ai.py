import asyncio
import socket

from openai import AsyncOpenAI

from feeluown.utils.aio import run_afn


async def a_handle_stream(stream):
    rsock, wsock = socket.socketpair()
    rr, rw = await asyncio.open_connection(sock=rsock)
    _, ww = await asyncio.open_connection(sock=wsock)

    async def write_task():
        async for chunk in stream:
            # When stream_options={'include_usage': True},
            # the last chunk.choices is empty.
            if chunk.choices:
                content = chunk.choices[0].delta.content or ''
                ww.write(content.encode('utf-8'))

        ww.write_eof()
        await ww.drain()
        ww.close()
        await ww.wait_closed()
        try:
            return chunk  # chunk may be undefined
        except NameError:
            return

    task = run_afn(write_task)
    return rr, rw, task


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
