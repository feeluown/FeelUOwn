#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cmd
import os
import sys
import readline

from socket_client import Client
from helpers import Helpers, ForeColors, Const


class CliShell(cmd.Cmd):

    def __init__(self):
        super().__init__()
        self.prompt = Const.ps1
        self.songs = None
        self.doc_header = "「暂时支持以下命令」"\
        "\n"\
        "「可以通过 help command_name 来查看命令的使用示例哦」"

    def connect_to_server(self, port=12100):
        if Client.connect(port=port):
            return True
        return False

    def do_play(self, query):
        """切换为播放状态或者播放一首特定的歌曲

        假设有一首歌的id是: 1314
        你可以通过以下命令播放你所指定的这首歌
        用法示例: 
            \033[92mfeeluown ☛  play 1314\033[0m
        你也可以不加参数，它可以让播放器从暂停状态切换为播放状态:
            \033[92mfeeluown ☛ play\033[0m
        """
        func = 'play()'
        if query != '':
            try:
                func = 'play(%d)' % int(query)
            except ValueError:
                Helpers.print_hint("参数必须是歌曲的 id")
                return

        Client.send(func)
        Client.recv()

    def complete_play(self, text, line, begidx, endidx):
        match_songs = list()
        if text != '':
            for song in self.songs:
                if str(song['id']).startswith(text):
                    match_songs.append(song)
        else:
            match_songs = self.songs
        song_ids = list()
        for song in match_songs:
            song_ids.append(str(song['id']))
        return song_ids

    def do_pause(self, query):
        """暂停播放歌曲"""
        Client.send('pause()')
        Client.recv()

    def do_play_next(self, query):
        """播放下一首歌曲"""
        Client.send('play_next()')
        Client.recv()

    def do_play_preview(self, query):
        """播放上一个歌曲"""
        Client.send('play_previous()')
        Client.recv()

    def do_search(self, query):
        """搜索歌曲、歌手、专辑 etc.
        
        用法示例: 
            \033[92mfeeluown ☛  search 刘德华\033[0m
        """
        if query.startswith('"'):
            query = query[1:-1]
        func = 'search("%s")' % query
        Client.send(func)
        data = Client.recv()
        songs = data.get('result', None)
        if type(songs) == list:
            self.songs = songs[:10]
            Helpers.print_music_list(songs)
        else:
            Helpers.print_hint("蛋疼，没有搜到...")

    def do_ls(self, query):
        """可以看到都有哪些指令可以用"""
        self.do_help(query)

    def do_clear(self, query):
        """清空屏幕"""
        os.system("clear")
        Helpers.show_title()

    def do_exit(self, query):
        """退出cli程序"""
        Client.close()
        print(ForeColors.magenta + "😋  bye ~ " + ForeColors.default)
        sys.exit(0)

    def show_current_playlist(self, query):
        """显示当前播放列表"""
        pass

    def default(self, query):
        Helpers.print_("😶  这命令是什么鬼")


if __name__ == '__main__':
    Helpers.show_title()
    CliShell().cmdloop()
