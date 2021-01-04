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
    author='Cosven',
    author_email='yinshaowen241@gmail.com',
    packages=find_packages(exclude=('tests*',)),
    py_modules=['mpv', 'mpv_old'],
    package_data={
        '': ['linux/*.xml',
             'icons/*.png',
             'icons/*.ico',
             'icons/*.icns',
             'themes/*.qss',
             'themes/*.colors',
             ]
    },
    python_requires=">=3.6",
    url='https://github.com/feeluown/FeelUOwn',
    keywords=['media', 'player', 'application', 'PyQt5', 'Python 3'],
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Environment :: X11 Applications :: Qt',
        "Topic :: Multimedia :: Sound/Audio",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
    # FIXME: depends on PyQt5
    #
    # The feeluown.compat module will choose the right package
    # for different python version
    install_requires=[
        'janus',
        'requests',
        'qasync',
        'tomlkit',
        'pydantic',

        'typing_extensions;python_version<"3.8"',
    ],
    extras_require={
        'battery': ['fuo-local>=0.2.1',
                    'fuo-xiami>=0.2.3',
                    'fuo-netease>=0.4.2',
                    'fuo-qqmusic>=0.2',
                    'fuo-kuwo>=0.1.1',
                    ],
        'macOS': ['pyobjc-framework-Cocoa', 'pyobjc-framework-Quartz'],
        'win32': ['pyshortcuts'],
        'webengine': ['PyQtWebEngine'],
        'dev': [
            # lint
            'flake8',
            'mypy',

            # unittest
            'pytest>=5.4.0',
            'pytest-runner',
            'pytest-cov',
            'pytest-asyncio',
            'pytest-qt',
            'pytest-mock',

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
        ]
    },
)
