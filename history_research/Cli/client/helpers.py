# -*- coding: utf-8 -*-

import sys


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


class Helpers(object):
    
    @classmethod
    def print_(cls, *args, **kw):
        print('           ', end='')
        print(*args, **kw)

    @staticmethod
    def print_success(text=''):
        print('😃  ' + ForeColors.green + text + ForeColors.default)

    @staticmethod
    def print_error(text=''):
        print('😨  ' + ForeColors.red + text + ForeColors.default)

    @staticmethod
    def print_hint(text):
        print('😝  ' + ForeColors.red + text + ForeColors.default)
    
    @classmethod
    def hint(cls, text):
        print(ForeColors.grey + "           " + text)

    @classmethod
    def welcome(cls):
        print("\t\t\t%s Welcome %s to %s feeluown %s cli" % (ForeColors.magenta,
            ForeColors.cyan, ForeColors.red, ForeColors.blue))

    @classmethod
    def show_title(cls):
        if sys.platform == "darwin":
            print("\t\t\t\t🎵  %s 🎵" % Const.colorful_name)
        elif sys.platform == "Linux":
            print("\t\t\t\t\033[91m♬  %s \033[94m♬" % Const.colorful_name)
        else:
            print("\t\t\t\t\033[91m♬  %s \033[94m♬" % Const.colorful_name)

    @classmethod
    def check_data(cls, data):
        if data['code'] == 200:
            cls.print_success()
        elif data['code'] == 404:
            cls.print_error()

    def print_music_list(songs):
        for i, song in enumerate(songs):
            if i >= 10:
                break
            index = i  
            id = str(song['id'])
            name = song['name']     # name 占22个位置
            name_len = 0
            for i, ch in enumerate(name):
                if 0x4e00 <= ord(ch) <= 0x9fff:
                    name_len += 2  # 一个汉字在终端的长度相当于两个英文
                    if name_len == 20:
                        name = name[:i] + '....'    # 22
                        name_len = 22
                        break
                    elif name_len == 21:
                        name = name[:i] + '...'  # 22
                        name_len = 22
                        break
                else:
                    name_len += 1
                    if name_len == 20:
                        name = name[:i] + '...'  # 22
                        name_len = 22
                        break


            artists = song['artists']
            artist_name = artists[0]['name']
            if len(artists) > 1:
                artist_name += '...'
    
            print(ForeColors.blue, index, ForeColors.default, end='')
            print(ForeColors.cyan, ' '*(10-len(id)) + id, ForeColors.default, end='')
            print(ForeColors.magenta, name + '*'*(22-name_len), ForeColors.default, end='')
            print(ForeColors.yellow, artist_name[:20] + ' '*(20-len(artist_name)), ForeColors.default)


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


