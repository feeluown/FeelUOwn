import os
import sys
import ctypes
from PyInstaller.utils.hooks import collect_data_files, collect_entry_point


assets_files = [
    '**/*.png',
    '**/*.qss',
    '**/*.svg',
    '**/*.ico',
    '**/*.icns',
    '**/*.colors',
    '**/*.mo',
]
datas, hiddenimports = collect_entry_point('fuo.plugins_v1')

if 'fuo_ytmusic' in hiddenimports:
    hiddenimports.append('ytmusicapi')

# aionowplaying is conditionally imported.
if os.name == 'nt':
    hiddenimports.append('aionowplaying')
    # pyinstaller can't detect 'aionowplaying.interface.windows' is imported.
    hiddenimports.append('aionowplaying.interface.windows')
if sys.platform == 'darwin':
    hiddenimports.append('aionowplaying.interface.macos')
    hiddenimports.append('feeluown.aionowplaying.macos')

# Collect feeluown's resource files, like icons, qss files, etc.
# Collect plugins' resource files.
datas += collect_data_files('feeluown', includes=assets_files)
for pkg in hiddenimports:
    datas += collect_data_files(pkg, includes=assets_files)


# Collect mpv dynamic-link library.
if os.name == 'nt':
    mpv_dylib = 'mpv-1.dll'
else:
    mpv_dylib = 'mpv'
mpv_dylib_path = ctypes.util.find_library(mpv_dylib)
binaries = [(mpv_dylib_path, '.'), ]
