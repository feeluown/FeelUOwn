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
        'feeluown.containers',
        'feeluown.components',
        'feeluown.plugins.qqmusic',
        'feeluown.plugins.neteasemusic',
        'feeluown.plugins.local',
        'feeluown.plugins.xiami',
        'feeluown.protocol',
        ],
    package_data={
        '': ['*.qss', '*.png', '../icons/*.png']
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
        'fuocore>=2.0.3',
        'requests',
        ],
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
                "feeluown=feeluown.__main__:main",
                "feeluown-genicon=feeluown.install:generate_icon",
                # "feeluown-update=feeluown.install:update"
            ]
        },
    )
