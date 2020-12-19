from typing import Union
from hashlib import sha256

import fsspec

from mpv import MPV


class CacheManager:
    def __init__(self, player: MPV, path: Union[str, list[str]]):
        self._player = player
        self._cache = fsspec.filesystem('filecache', target_protocol='http',
                                        cache_storage=path, check_files=False)

    def get(self, remote_uri: str):
        stream = sha256(remote_uri.encode()).hexdigest()

        @self._player.python_stream(stream)
        def read_from_cache():
            with self._cache.open(remote_uri) as f:
                while True:
                    yield f.read(1024 * 1024)

        return f'python://{stream}'


if __name__ == '__main__':
    # Extra requirements: fsspec, aiohttp
    player = MPV()
    uri = 'https://other-web-ri01-sycdn.kuwo.cn/6cc8fb160a0d5dcbe1ba62f753a0f49b/5fddb036/resource/n2/71/16/340690382.mp3'
    cache = CacheManager(player, '/tmp/fuo')
    play_uri = cache.get(uri)
    player.play(play_uri)
    player.wait_for_playback()
