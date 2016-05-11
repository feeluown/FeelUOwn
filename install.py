#! /usr/bin/env python3

import os


def install_sys_dep():
    packages = ['python3-pyqt5',
                'python3-pyqt5.qtmultimedia',
                'libqt5multimedia5-plugins',
                'fcitx-frontend-qt5',
                'gstreamer0.10-plugins-good',
                'gstreamer0.10-plugins-bad',
                'gstreamer0.10-plugins-ugly',
                'python3-setuptools',
                'python3-pip']

    print('Download and install software dependency.')
    os.system('sudo apt-get install -y {packages} 1>/dev/null'
              .format(packages=' '.join(packages)))

    print('Download and install python dependency')
    os.system('pip3 install -r requirements.txt 1>/dev/null')


def generate_icon():
    print('Generate icon, then you can see app in apps list.')
    current_path = os.getcwd()
    feeluown_dir = current_path + '/feeluown'
    feeluown_icon = feeluown_dir + '/feeluown.png'
    icon_string = '#!/usr/bin/env xdg-open\n'\
                  '[Desktop Entry]\n'\
                  'Type=Application\n'\
                  'Name=FeelUOwn\n'\
                  'Comment=FeelUOwn Launcher\n'\
                  'Exec=sh -c "PYTHONPATH={current_path}: python3 -m feeluown"\n'\
                  'Icon={feeluown_icon}\n'\
                  'Categories=AudioVideo;Audio;Player;Qt;\n'\
                  'Terminal=false\n'\
                  'StartupNotify=true\n'\
                  .format(feeluown_icon=feeluown_icon,
                          current_path=current_path)
    f_path = os.path.expanduser('~') +\
        '/.local/share/applications/FeelUOwn.desktop'
    if os.path.exists(f_path):
        os.remove(f_path)
    with open(f_path, 'w') as f:
        f.write(icon_string)
    os.system('chmod +x %s' % f_path)


install_sys_dep()
generate_icon()
