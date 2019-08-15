#!/usr/bin/env python3

from setuptools import setup

import feeluown


setup(
    name='feeluown',
    version=feeluown.__version__,
    description='*nix music player',
    author='Cosven',
    author_email='yinshaowen241@gmail.com',
    packages=[
        'feeluown',
        'feeluown.entry_points',
        'feeluown.widgets',
        'feeluown.widgets.statusline_items',
        'feeluown.uimodels',
        'fuocore',
        'fuocore.cmds',
        'fuocore.protocol',
        ],
    py_modules=['mpv'],
    package_data={
        '': ['*.qss', '*.png', '../icons/*.png', 'themes/*.qss']
        },
    url='https://github.com/cosven/FeelUOwn',
    keywords=['media', 'player', 'application', 'PyQt5', 'Python 3'],
    classifiers=(
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Environment :: X11 Applications :: Qt',
        ),
    # FIXME depends on PyQt5
    install_requires=[
        'quamash>=0.5.5',
        'janus',
        'requests',
        'pyopengl',
        ],
    extras_require={
        'battery': ['fuo-local>=0.1.1',
                    'fuo-xiami>=0.1.2',
                    'fuo-netease>=0.2',
                    'fuo-qqmusic>=0.1.2'],
        'macOS': ['pyobjc-framework-Cocoa', 'pyobjc-framework-Quartz']
    },
    tests_require=['pytest-runner',
                   'pytest',
                   'pytest-cov',
                   'pytest-asyncio',
                   'pytest-qt',
                   'pytest-mock'],
    entry_points={
        'console_scripts': [
                "feeluown=feeluown.__main__:main",
                "fuo=feeluown.__main__:main",
                "feeluown-genicon=feeluown.install:generate_icon",
                # "feeluown-update=feeluown.install:update"
            ]
        },
    )
