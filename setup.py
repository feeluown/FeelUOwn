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
        'feeluown.protocol',
        'fuocore',
        ],
    py_moduels=['mpv'],
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
        'requests',
        'pyopengl',
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
