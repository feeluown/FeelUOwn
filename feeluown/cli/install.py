#! /usr/bin/env python3

import shutil
import os
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve()
ICONS_DIR = HERE.parent.parent / 'icons'

mac_shell_str = """#!/bin/bash
/usr/local/bin/feeluown --log-to-file
"""

mac_plist_str = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>BuildMachineOSBuild</key>
    <string>18A353d</string>
    <key>CFBundleDevelopmentRegion</key>
    <string>zh_CN</string>
    <key>CFBundleExecutable</key>
    <string>feeluown</string>
    <key>CFBundleIconFile</key>
    <string>feeluown</string>
    <key>CFBundleIdentifier</key>
    <string>com.fuo.feeluown</string>
</dict>
</plist>
"""  # noqa: E501

win_linux_icon = """#!/usr/bin/env xdg-open
[Desktop Entry]
Type=Application
Name=FeelUOwn
Comment=FeelUOwn Launcher
Exec=python3 -m feeluown --log-to-file
Icon={feeluown_icon}
Categories=AudioVideo;Audio;Player;Qt;
Terminal=false
StartupNotify=true
"""


def write_file(path, content):
    try:
        with open(path, 'w') as f:
            f.write(content)
        os.system('chmod +x {}'.format(path))
    except PermissionError:
        print('Please use sudo')
        raise


def gen_for_mac():
    app_path = pathlib.Path.home() / 'Desktop' / 'FeelUOwn.app'
    content_dir = app_path / 'Contents'
    os_dir = content_dir / 'MacOS'
    resource_dir = content_dir / 'Resources'
    for p in [app_path, content_dir, os_dir, resource_dir]:
        p.mkdir() if not p.exists() else None
    info_plist = content_dir / 'info.plist'
    run_file = os_dir / 'feeluown'
    from_icon = ICONS_DIR / 'feeluown.icns'
    to_icon = resource_dir / 'feeluown.icns'

    write_file(run_file, mac_shell_str)
    write_file(info_plist, mac_plist_str)
    shutil.copy(from_icon, to_icon)


def gen_for_win_linux():
    DESKTOP_FILE = 'feeluown.desktop'
    from_icon = ICONS_DIR / 'feeluown.png'
    to_icon = pathlib.Path.home() / '.FeelUOwn' / 'feeluown.png'
    shutil.copy(from_icon, to_icon)

    icon_string = win_linux_icon.format(feeluown_icon=to_icon)
    f_path = pathlib.Path.home() / '.local/share/applications' / DESKTOP_FILE
    write_file(f_path, icon_string)

    en_desktop_path = pathlib.Path.home() / 'Desktop'
    cn_desktop_path = pathlib.Path.home() / '桌面'
    desktop_file = None
    if en_desktop_path.exists():
        desktop_file = en_desktop_path / DESKTOP_FILE
    if cn_desktop_path.exists():
        desktop_file = cn_desktop_path / DESKTOP_FILE
    if desktop_file:
        shutil.copy(f_path, desktop_file)
    os.system('chmod +x {}'.format(desktop_file))


def gen_for_win32():
    from pyshortcuts import make_shortcut

    # NOTE: do not use the pythonw.exe under sys.prefix, if Python is installed
    # through window app store, the Python will have 'abnormal' behaviour::
    #
    #   the normal python.exe we run in cmd is located in directory like following:
    #   C:\Users\user\AppData\Local\Microsoft\WindowsApps\
    #     PythonSoftwareFoundation.Python.3.8_qbz5n2kfra8p0\pythonw.exe
    #
    #   but the python sys.prefix is like:
    #   C:\Program Files\WindowsApps\
    #     PythonSoftwareFoundation.Python.3.8_3.8.496.0_x64__qbz5n2kfra8p0
    #
    #   user can't directly run the python.exe under sys.prefix, windows
    #   will tell user it has no priviledge to run this program
    pyexe = os.path.join(os.path.dirname(sys.executable), 'pythonw')
    command = '{} -m feeluown'.format(pyexe)
    ico = HERE.parent.parent / 'icons' / 'feeluown.ico'
    name = 'FeelUOwn'
    make_shortcut(command, name=name, icon=ico, terminal=False)


def generate_icon():
    print('Generate icon, then you can see app on desktop.')
    if sys.platform.lower() == 'darwin':
        gen_for_mac()
    elif sys.platform == 'win32':
        gen_for_win32()
    else:
        gen_for_win_linux()
    print('Generate success.')


if __name__ == '__main__':
    generate_icon()
