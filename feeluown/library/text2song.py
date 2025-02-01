import uuid
import json

from .models import BriefSongModel, ModelState
from feeluown.utils.utils import elfhash


class AnalyzeError(Exception):
    pass


def analyze_text(text):
    def json_fn(each):
        try:
            return each['title'], each['artists_name']
        except KeyError:
            return None

    def line_fn(line):
        parts = line.split('|')
        if len(parts) == 2 and parts[0]:  # title should not be empty
            return (parts[0], parts[1])
        return None

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        lines = text.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if first_line in ('---', '==='):
                parse_each_fn = line_fn
                items = [each.strip() for each in lines[1:] if each.strip()]
            elif first_line == '```json':
                try:
                    items = json.loads(text[7:-3])
                except json.JSONDecodeError:
                    raise AnalyzeError('invalid JSON content inside code block')
                parse_each_fn = json_fn
            else:
                raise AnalyzeError('invalid JSON content')
    else:
        if not isinstance(data, list):
            # should be like [{"title": "xxx", "artists_name": "yyy"}]
            raise AnalyzeError('content has invalid format')
        parse_each_fn = json_fn
        items = data

    err_count = 0
    songs = []
    for each in items:
        result = parse_each_fn(each)
        if result is not None:
            title, artists_name = result
            song = new_song_model(title, artists_name)
            songs.append(song)
        else:
            err_count += 1
    return songs, err_count
