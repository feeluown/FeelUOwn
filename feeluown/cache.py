from hashlib import sha256
from typing import Union

import fsspec

from mpv import MPV


class CacheManager:
    def __init__(self, path: Union[str, list[str]]):
        self._cache = fsspec.filesystem('filecache', target_protocol='http',
                                        cache_storage=path, check_files=False)

    def open(self, remote_uri: str):
        return self._cache.open(remote_uri)


class MpvCacheManager(CacheManager):
    def __init__(self, path: Union[str, list[str]], mpv: MPV):
        super(MpvCacheManager, self).__init__(path)
        self._mpv = mpv

    def get(self, remote_uri: str):
        stream = sha256(remote_uri.encode()).hexdigest()

        @self._mpv.python_stream(stream)
        def read_from_cache():
            with super(MpvCacheManager, self).open(remote_uri) as f:
                while True:
                    yield f.read(1024 * 1024)

        return f'python://{stream}'


if __name__ == '__main__':
    # Extra requirements: fsspec, aiohttp
    player = MPV()
    uri = 'https://other-web-ri01-sycdn.kuwo.cn/6cc8fb160a0d5dcbe1ba62f753a0f49b/5fddb036/resource/n2/71/16/340690382.mp3'
    cache = MpvCacheManager('/tmp/fuo', player)
    play_uri = cache.get(uri)
    player.play(play_uri)
    player.wait_for_playback()
