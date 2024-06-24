import logging
from typing import Optional, List, Any

from yt_dlp import YoutubeDL

from feeluown.media import Media

logger = logging.getLogger(__name__)


class Ytdl:
    def __init__(self, rules: Optional[List[Any]] = None):
        self._default_audio_ytdl_opts = {
            'logger': logger,
            # The following two options may be only valid for select_audio API.
            # Remove these two options if needed.
            'format': 'm4a/bestaudio/best',
            'postprocessors': [{  # Extract audio using ffmpeg
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }]
        }
        # For example::
        #    [{'name': 'match_source',
        #      'pattern': 'xxx',
        #      'http_proxy': 'http://127.0.0.1:7890'},]
        # TODO: valid rules
        self._rules = rules or []

    def select_audio(self, url, _: Optional[str] = None, source='') -> Optional[Media]:
        matched_rule = None
        if isinstance(self._rules, list) and self._rules:
            for rule in self._rules:
                if rule['name'] == 'match_source' and source == rule['pattern']:
                    matched_rule = rule
        if matched_rule is None:
            return

        http_proxy = matched_rule.get('http_proxy')
        ytdl_opts = {}
        ytdl_opts.update(self._default_audio_ytdl_opts)
        ytdl_opts['proxy'] = http_proxy
        with YoutubeDL(ytdl_opts) as inner:
            info = inner.extract_info(url, download=False)
            if info:
                media_url = info['url']
                if media_url:
                    # NOTE(cosven): do not set http headers, otherwise it can't play.
                    # Tested with 'https://music.youtube.com/watch?v=vKwowKeEv5w'
                    return Media(media_url,
                                 format=info['ext'],
                                 bitrate=int(info['abr']),
                                 http_proxy=http_proxy)
            return None


if __name__ == '__main__':
    # A E2E test case for YTDL, this should print a playable url.
    rules = [{'name': 'match_source',
              'pattern': 'ytmusic',
              'http_proxy': 'http://127.0.0.1:7890'},]

    ytdl = Ytdl(rules)
    url = 'https://music.youtube.com/watch?v=vKwowKeEv5w'
    media = ytdl.select_audio(url, None, 'ytmusic')
    print(media.url)
