# -*- coding: utf-8 -*-


def analysis(command):
    words = command.split(' ')
    for word in words:
        if word == '':
            words.remove(word)
    return words


def words_to_func(words):
    func_name = words[0]
    args = ""
    for i in range(1, len(words)):
        args += words[i]
        if i is not len(words)-1:
            args += ', '
    func = func_name + '(' + args + ')'
    return func
