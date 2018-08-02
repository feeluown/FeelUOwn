#! /usr/bin/env python3

import shutil
import os


def generate_icon():
    print('Generate icon, then you can see app in apps list.')
    os.system('mkdir -p ~/.FeelUOwn')
    DESKTOP_FILE = 'feeluown.desktop'
    current_path = os.path.abspath(os.path.dirname(__file__))
    icon = current_path + '/feeluown.png'
    feeluown_home_dir = os.path.expanduser('~') + '/.FeelUOwn'
    feeluown_icon = feeluown_home_dir + '/feeluown.png'
    shutil.copy(icon, feeluown_icon)

    icon_string = '#!/usr/bin/env xdg-open\n'\
                  '[Desktop Entry]\n'\
                  'Type=Application\n'\
                  'Name=FeelUOwn\n'\
                  'Comment=FeelUOwn Launcher\n'\
                  'Exec=python3 -m feeluown --log-to-file\n'\
                  'Icon={feeluown_icon}\n'\
                  'Categories=AudioVideo;Audio;Player;Qt;\n'\
                  'Terminal=false\n'\
                  'StartupNotify=true\n'\
                  .format(feeluown_icon=feeluown_icon)
    f_path = os.path.expanduser('~') +\
        '/.local/share/applications/' + DESKTOP_FILE
    try:
        with open(f_path, 'w') as f:
            f.write(icon_string)
        os.system('chmod +x %s' % f_path)
    except PermissionError:
        print('Please use sudo')
    en_desktop_path = os.path.expanduser('~') + '/Desktop'
    cn_desktop_path = os.path.expanduser('~') + '/桌面'
    if os.path.exists(en_desktop_path):
        desktop_f = en_desktop_path + '/' + DESKTOP_FILE
    if os.path.exists(cn_desktop_path):
        desktop_f = cn_desktop_path + '/' + DESKTOP_FILE
    shutil.copy(f_path, desktop_f)
    os.system('chmod +x %s' % desktop_f)
    print('Generate success.')


if __name__ == '__main__':
    generate_icon()
