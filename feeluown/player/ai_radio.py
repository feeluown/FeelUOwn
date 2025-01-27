import logging
from typing import TYPE_CHECKING

from feeluown.library import BriefSongModel, reverse
from feeluown.library.text2song import analyze_text, AnalyzeError
from feeluown.utils.utils import DedupList

try:
    from openai import OpenAI
except ImportError:
    AI_RADIO_SUPPORTED = False
else:
    AI_RADIO_SUPPORTED = True

if TYPE_CHECKING:
    from feeluown.app import App


logger = logging.getLogger(__name__)


def song2line(song: BriefSongModel):
    line = reverse(song, as_line=True)
    parts = line.split('#', 1)
    if len(parts) >= 2:
        return parts[1]
    return None


class AIRadio:
    def __init__(self, app: 'App'):
        self._app = app

        self._messages = []
        self._unliked_songs = DedupList()
        self._app.playlist.songs_removed.connect(self._on_songs_removed, weak=True)

        self._messages.append({"role": "system",
                               "content": self._app.config.AI_RADIO_PROMPT})

    def fetch_songs_func(self, _):
        client = OpenAI(
            api_key=self._app.config.OPENAI_API_KEY,
            base_url=self._app.config.OPENAI_API_BASEURL,
        )
        msg_lines = []
        for song in self._app.playlist.list():
            if self._app.playlist.is_bad(song):
                continue
            line = song2line(song)
            if line is not None:
                msg_lines.append(line)
        msg = '\n'.join(msg_lines)
        # umsg_lines = []
        # for song in self._unliked_songs[-10:]:
        #     line = song2line(song)
        #     if line is not None:
        #         umsg_lines.append(line)
        # umsg = '\n'.join(umsg_lines) if umsg_lines else '暂时没有不喜欢的歌曲'
        self._messages.append({
            "role": "user",
            "content": (
                f"当前播放列表内容如下：\n{msg}")
        })
        response = client.chat.completions.create(
            model=self._app.config.OPENAI_MODEL,
            messages=self._messages,
        )
        msg = response.choices[0].message
        self._messages.append(msg)
        for _msg in self._messages[-2:]:
            logger.info(f"AI radio, message: {dict(_msg)['content']}")
        try:
            songs, err_count = analyze_text(str(msg.content))
        except AnalyzeError:
            logger.exception('Analyze AI response failed')
            return []
        logger.info(f'AI recommend {len(songs)} songs, err_count={err_count}')
        return songs

    def _on_songs_removed(self, index, count):
        songs = self._app.playlist[index: index + count]
        self._unliked_songs.extend(songs)
