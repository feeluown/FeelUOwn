import os
import ctypes
from PyInstaller.utils.hooks import collect_data_files, collect_entry_point


datas, hiddenimports = collect_entry_point('fuo.plugins_v1')

# Collect feeluown's resource files, like icons, qss files, etc.
# Collect plugins' resource files.
datas += collect_data_files('feeluown')
for pkg in hiddenimports:
    datas += collect_data_files(pkg)

# Collect mpv dynamic-link library.
if os.name == 'nt':
    mpv_dylib = 'mpv-1.dll'
else:
    mpv_dylib = 'mpv'
mpv_dylib_path = ctypes.util.find_library(mpv_dylib)
binaries = [(mpv_dylib_path, '.'), ]