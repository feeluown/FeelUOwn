# -*- coding: utf-8 -*-

from cmd_resolution import analysis, words_to_func


def test_analysis():
    words = analysis(' play  1213 ')
    assert words == ['play', '1213']


def test_words_to_func():
    words = ['play', '1213', 'hello']
    func = words_to_func(words)
    assert func == 'play(1213, hello)'
