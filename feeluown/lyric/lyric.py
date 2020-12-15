# -*- coding: utf-8 -*-

import re


def parse(content):
    """
    Reference: https://github.com/osdlyrics/osdlyrics/blob/master/python/lrc.py

    >>> parse("[00:00.00] 作曲 : 周杰伦\\n[00:01.00] 作词 : 周杰伦\\n")
    {0.0: ' 作曲 : 周杰伦', 1000.0: ' 作词 : 周杰伦'}
    """
    ms_sentence_map = dict()
    sentence_pattern = re.compile(r'\[(\d+(:\d+){0,2}(\.\d+)?)\]')
    lines = content.splitlines()
    for line in lines:
        m = sentence_pattern.search(line, 0)
        if m:
            time_str = m.group(1)
            mileseconds = 0
            unit = 1000
            t_seq = time_str.split(':')
            t_seq.reverse()
            for num in t_seq:
                mileseconds += float(num) * unit
                unit *= 60
            sentence = line[m.end():]
            ms_sentence_map[mileseconds] = sentence
    return ms_sentence_map
