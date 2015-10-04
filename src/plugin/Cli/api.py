# -*- coding: utf-8 -*-


from interfaces import ControllerApi


def play(mid=None):
    if mid is None:
        ControllerApi.play_specific_song_by_mid(mid)
    else:
        ControllerApi.player.play_or_pause()
