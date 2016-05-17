#! /usr/bin/env python3

import platform
import shutil
import os


def install_sys_dep():

    def _get_gstreamer(gstreamer_version='0.10'):
        v_package = ['gstreamer{0}-plugins-good'.format(gstreamer_version),
                     'gstreamer{0}-plugins-bad'.format(gstreamer_version),
                     'gstreamer{0}-plugins-ugly'.format(gstreamer_version)]
        return v_package

    packages = ['python3-pyqt5',
                'python3-pyqt5.qtmultimedia',
                'libqt5multimedia5-plugins',
                'fcitx-frontend-qt5']

    linux_distro = platform.linux_distribution()
    if linux_distro[0] in ('Deepin') or 'ubuntu' in linux_distro[0].lower():
        print('Download and install software dependency.')
        os.system('sudo apt-get install -y {packages} 1>/dev/null'
                  .format(packages=' '.join(packages)))
        if linux_distro[1] >= '16.04':
            gstreamer_version = '1.0'
        else:
            gstreamer_version = '0.10'
        gstreamer_packages = _get_gstreamer(gstreamer_version)
        packages = packages + gstreamer_packages
        os.system('sudo apt-get install -y {packages} 1>/dev/null'
                  .format(packages=' '.join(packages)))
        print('\ninstall finished ~')
    else:
        print('You should install these packages by yourself, '
              'as your linux may not a debian distribution\n')
        packages = packages + _get_gstreamer()
        for i, p in enumerate(packages):
            print(i, ': ', p)
        print('\npackage name may be different among different systems')


def generate_icon():
    print('Generate icon, then you can see app in apps list.')
    DESKTOP_FILE = 'feeluown.desktop'
    current_path = os.getcwd()
    feeluown_dir = current_path + '/feeluown'
    feeluown_icon = feeluown_dir + '/feeluown.png'
    icon_string = '#!/usr/bin/env xdg-open\n'\
                  '[Desktop Entry]\n'\
                  'Type=Application\n'\
                  'Name=FeelUOwn\n'\
                  'Comment=FeelUOwn Launcher\n'\
                  'Exec=sh -c "python3 -m feeluown"\n'\
                  'Icon={feeluown_icon}\n'\
                  'Categories=AudioVideo;Audio;Player;Qt;\n'\
                  'Terminal=false\n'\
                  'StartupNotify=true\n'\
                  .format(feeluown_icon=feeluown_icon,
                          current_path=current_path)
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
