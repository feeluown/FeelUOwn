#!/usr/bin/env python3

from setuptools import setup, find_packages
from os import path

import feeluown

current_directory = path.abspath(path.dirname(__file__))
with open(path.join(current_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='feeluown',
    version=feeluown.__version__,
    description='*nix music player',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="GPL-3.0",
    author='feeluown',
    author_email='yinshaowen241@gmail.com',
    packages=find_packages(exclude=('tests*',)),
    package_data={
        '': ['nowplaying/linux/*.xml',
             'gui/assets/icons/*.png',
             'gui/assets/icons/*.ico',
             'gui/assets/icons/*.icns',
             'gui/assets/themes/*.qss',
             'gui/assets/themes/*.colors',
             ]
    },
    python_requires=">=3.8",
    url='https://github.com/feeluown/FeelUOwn',
    keywords=['media', 'player', 'application', 'PyQt5', 'music'],
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3 :: Only',
        'Environment :: X11 Applications :: Qt',
        "Topic :: Multimedia :: Sound/Audio",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
    # FIXME: depends on PyQt5
    # - PyQt5.QtWidgets/QtCore/QtGui
    # - PyQt5.QtSvg
    # - PyQt5.QtOpenGL
    #
    # The feeluown.compat module will choose the right package
    # for different python version
    install_requires=[
        'janus',
        'requests',
        'qasync',
        'tomlkit',
        'packaging',
        'pydantic>=1.10',  # v1 and v2 are both ok.
        'mutagen>=1.37',
    ],
    extras_require={
        'battery': ['fuo-netease>=1.0.3',
                    'fuo-qqmusic>=1.0.5',
                    'fuo-ytmusic>=0.4.4',
                    # 'fuo-kuwo>=0.1.1',
                    # https://github.com/BruceZhang1993/feeluown-bilibili
                    'feeluown-bilibili>=0.4.1',
                    ],
        'ai': [
            'openai>=1.50',
        ],
        'qt': [
            'PyQt5',
        ],
        'macOS': [
            'aionowplaying>=0.10',
        ],
        'win32': [
            'pyshortcuts',
            'aionowplaying>=0.10',
        ],
        'jsonrpc': ['json-rpc'],
        'webserver': ['sanic', 'json-rpc'],
        'webengine': ['PyQtWebEngine'],
        # Load cookies from chrome/firefox/...
        'cookies': [
            'yt-dlp',
        ],
        'ytdl': [
            'yt-dlp',
        ],
        'dev': [
            # lint
            'flake8',
            'pylint',
            'mypy',
            # pyqt5-stubs seems more accurate than the stubs packaged in PyQt5 package.
            # For example, the stubs in PyQt5 has wrong type hint for Qt.ItemIsSelectable.
            # Some pyqt5 package installed by system package manager may not contain stubs.
            'pyqt5-stubs',

            # unittest
            'pytest>=5.4.0',
            'pytest-runner',
            'pytest-cov',
            'pytest-asyncio',
            'pytest-qt',
            'pytest-mock',
            'pytest-benchmark>=3.4.1',

            # docs
            'sphinx',
            'sphinx_rtd_theme',
        ],
    },
    entry_points={
        'console_scripts': [
            "feeluown=feeluown.__main__:main",
            "fuo=feeluown.__main__:main",
            "feeluown-genicon=feeluown.cli.install:generate_icon",
            # "feeluown-update=feeluown.install:update"
        ],
        'fuo.plugins_v1': [
            'local = feeluown.local',
        ],
        # https://pyinstaller.org/en/stable/hooks.html
        'pyinstaller40': [
            'hook-dirs = feeluown.pyinstaller.hook:get_hook_dirs',
        ],
    },
)
