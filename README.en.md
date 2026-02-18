## FeelUOwn - feel your own

[![Documentation Status](https://readthedocs.org/projects/feeluown/badge/?version=latest)](http://feeluown.readthedocs.org)
[![Build Status](https://github.com/feeluown/feeluown/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/feeluown/FeelUOwn)
[![Coverage Status](https://coveralls.io/repos/github/feeluown/FeelUOwn/badge.svg)](https://coveralls.io/github/feeluown/FeelUOwn)
[![PyPI](https://img.shields.io/pypi/v/feeluown.svg)](https://pypi.python.org/pypi/feeluown)
[![python](https://img.shields.io/pypi/pyversions/feeluown.svg)](https://pypi.python.org/pypi/feeluown)

FeelUOwn is a stable, user-friendly, and highly customizable music player.

[![macOS Preview](https://github.com/user-attachments/assets/6d96c655-e35b-46d8-aaec-4d4dc202347f)](https://www.bilibili.com/video/av46787694/)

### Features

- Stable and Easy to Use:
  - One-click installation, packages available for all popular platforms (e.g., Arch Linux, Windows, macOS, etc.)
  - Plugins for various media resource platforms, making full and reasonable use of free resources across the web (e.g., YouTube Music, etc.)
  - Comprehensive basic features, such as desktop lyrics, intelligent resource replacement, multiple quality selection, NowPlaying protocol, etc.
  - Core modules have good test coverage, and core interfaces maintain good backward compatibility
  - Powered by large models: AI radio, natural language to playlist conversion, etc.
- High Playability:
  - Provides an interactive control protocol based on TCP
  - Provides an MCP server (experimental) for programmatic player/resource control
  - Text-based playlists, easy to share with friends and sync across devices
  - Supports Python-based configuration file `.fuorc`, similar to `.vimrc` and `.emacs`

### Quick Start

Install FeelUOwn and its extensions with one command using your system package manager!

For Arch Linux and macOS, you can install it as follows:
```sh
# Arch Linux
yay -S feeluown          # Install the stable version; the latest version package is named feeluown-git
yay -S feeluown-netease  # Install other extensions as needed
yay -S feeluown-ytmusic
yay -S feeluown-bilibili

# macOS (It is recommended to first try downloading the pre-built package from the Release page!)
brew tap feeluown/feeluown
brew install feeluown --with-battery # Install FeelUOwn and extensions
feeluown genicon                     # Generate a FeelUOwn icon on the desktop
```

Windows and macOS users can download pre-built binaries from the Release page.
Linux distributions such as Gentoo, NixOS, Debian, openSUSE, etc. also support installation via their system package managers!
For details, please refer to the documentation: https://feeluown.readthedocs.io/, and you're also welcome to join the developer/user [community](https://t.me/joinchat/H7k12hG5HYsGy7RVvK_Dwg).

### Disclaimer

FeelUOwn (hereinafter referred to as “the Software”) is a personal media resource playback tool. All functions and materials provided by the Software may not be used for any commercial purposes. Users are free to choose whether to use the software provided by this product. If a user downloads, installs, and uses the Software, it indicates that the user trusts the software author. The software author is not liable for any form of loss or damage to the user or others for any reason during the use of the Software.

Any organization or individual that believes that the functions provided by the Software may infringe on their legitimate rights and interests should promptly provide written feedback to the FeelUOwn organization, along with identification, proof of ownership, and detailed evidence of infringement. Upon receipt of the above legal documents, the FeelUOwn organization will remove the alleged infringing content as soon as possible. (Contact: yinshaowen241 [at] gmail [dot] com)
