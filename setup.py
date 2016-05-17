#!/usr/bin/env python3
import glob
import os

from setuptools import setup, find_packages
import feeluown

print(find_packages('feeluown'))

setup(
    name='feeluown',
    version='1.0.0',
    description='*nix music player',
    author='Cosven',
    author_email='cosven.yin@gmail.com',
    packages=[
        'feeluown',
        'feeluown.libs',
        'feeluown.libs.widgets',
        'feeluown.plugins.neteasemusic',
        ],
    data_files=[
        ('feeluown/themes',
         glob.glob(os.path.join('.', 'feeluown/themes', '*'))),
        ],
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
            ]
        },
    )
