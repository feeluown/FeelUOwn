#!/usr/bin/env python3

from setuptools import setup

import feeluown


setup(
    name='feeluown',
    version=feeluown.__version__,
    description='*nix music player',
    author='Cosven',
    author_email='cosven.yin@gmail.com',
    packages=[
        'feeluown',
        'feeluown.libs',
        'feeluown.libs.widgets',
        'feeluown.plugins.neteasemusic',
        ],
    package_data={
        '': ['themes/*.colorscheme', '*.png']
        },
    url='https://github.com/cosven/FeelUOwn',
    keywords=['media', 'player', 'application', 'PyQt5', 'python3'],
    classifiers=(
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Environment :: X11 Applications :: Qt',
        ),
    # FIXME depends on PyQt5 , but cannot put that in a setup.py
    install_requires=[
        'quamash>=0.5.5',
        ],
    entry_points={
        'console_scripts': [
                "feeluown=feeluown.__main__:main",
                "feeluown-install-dev=feeluown.install:install_sys_dep",
                "feeluown-genicon=feeluown.install:generate_icon",
                "feeluown-update=feeluown.install:update"
            ]
        },
    )
