#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cmd
import os
import sys
import platform


class Style(object):
    bold = '\033[1m'
    underline = '\033[4m'


class ForeColors(object):
    red = '\033[91m'
    green = '\033[92m'
    blue = '\033[94m'
    cyan = '\033[96m'
    white = '\033[97m'
    yellow = '\033[93m'
    magenta = '\033[95m'
    grey = '\033[90m'
    black = '\033[90m'
    default = '\033[0m'


class BackColors(object):
    red = '\033[41m'
    green = '\033[42m'
    blue = '\033[44m'
    cyan = '\033[46m'
    white = '\033[47m'
    yellow = '\033[43m'
    magenta = '\033[45m'
    grey = '\033[40m'
    black = '\033[40m'
    default = '\033[49m'


class Const(object):
    name = "feeluown"
    colorful_name = ForeColors.red + 'feel' + \
        ForeColors.cyan + 'ʊ' + \
        ForeColors.blue + 'own' + \
        ForeColors.default
    ps1 = ForeColors.red + 'feel' + \
        ForeColors.cyan + 'ʊ' + \
        ForeColors.blue + 'own' + \
        ForeColors.green + ' ☛ ' + \
        ForeColors.default


class Helpers(object):
    
    @classmethod
    def print_(cls, *args, **kw):
        print("           ", end='')
        print(*args, **kw)
    
    @classmethod
    def hint(cls, text):
        print(ForeColors.grey + "           " + text)

    @classmethod
    def show_title(cls):
        if sys.platform == "darwin":
            print("\t\t\t\t\033[91m♬  %s \033[94m♬" % Const.colorful_name)
            print("\t\t\t\t🎵  %s 🎵" % Const.colorful_name)
        elif sys.platform == "Linux":
            print("\t\t\t\t\033[91m♬  %s \033[94m♬" % Const.colorful_name)
        else:
            print("\t\t\t\t\033[91m♬  %s \033[94m♬" % Const.colorful_name)

    

class CliShell(cmd.Cmd):

    def __init__(self):
        super().__init__()
        self.prompt = Const.ps1
        self.doc_header = "「暂时支持以下命令」"\
        "\n"\
        "「可以通过 help command_name 来查看命令的使用示例哦」"

    def do_play(self, query):
        """切换为播放状态或者播放一首特定的歌曲

        假设有一首歌的id是: 1314
        你可以通过以下命令播放你所指定的这首歌
        用法示例: 
            \033[92mfeeluown ☛  play 1314\033[0m
        你也可以不加参数，它可以让播放器从暂停状态切换为播放状态:
            \033[92mfeeluown ☛ play\033[0m
        """
        pass

    def do_pause(self, query):
        """暂停播放歌曲"""
        Helpers.hint("已经暂停播放")
        pass

    def do_play_next(self, query):
        """播放下一首歌曲"""
        pass

    def do_play_preview(self, query):
        """播放上一个歌曲"""
        pass

    def do_ls(self, query):
        """可以看到都有哪些指令可以用"""
        self.do_help(query)

    def do_clear(self, query):
        """清空屏幕"""
        os.system("clear")
        Helpers.show_title()

    def do_exit(self, query):
        """退出cli程序"""
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
