#! /usr/bin/env python3

import platform
import shutil
import os


def install_sys_dep():

    packages = ['python3-pyqt5',
                'python3-pyqt5.qtmultimedia',
                'libqt5multimedia5-plugins',
                'fcitx-frontend-qt5',
                'mpv']

    linux_distro = platform.linux_distribution()
    if linux_distro[0] in ('Deepin') or 'ubuntu' in linux_distro[0].lower():
        print('Download and install software dependency.')
        os.system('sudo apt-get install -y {packages} 1>/dev/null'
                  .format(packages=' '.join(packages)))
        os.system('sudo apt-get install -y {packages} 1>/dev/null'
                  .format(packages=' '.join(packages)))
        print('\ninstall finished ~')
    else:
        print('You should install these packages by yourself, '
              'as your linux may not a debian distribution\n')
        for i, p in enumerate(packages):
            print(i, ': ', p)
        print('\npackage name may be different among different systems')


def generate_icon():
    print('Generate icon, then you can see app in apps list.')
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
                  'Exec=python3 -m feeluown\n'\
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
    print('gen finished')


def update():
    os.system('sudo -H pip3 install --upgrade feeluown')
    os.system('feeluown-install-dev')
    os.system('feeluown-genicon')

if __name__ == '__main__':
    install_sys_dep()
    generate_icon()
