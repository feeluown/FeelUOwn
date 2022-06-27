## FeelUOwn - feel your own

[![Documentation Status](https://readthedocs.org/projects/feeluown/badge/?version=latest)](http://feeluown.readthedocs.org)
[![Build Status](https://github.com/feeluown/feeluown/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/feeluown/FeelUOwn)
[![Coverage Status](https://coveralls.io/repos/github/feeluown/FeelUOwn/badge.svg)](https://coveralls.io/github/feeluown/FeelUOwn)
[![PyPI](https://img.shields.io/pypi/v/feeluown.svg)](https://pypi.python.org/pypi/feeluown)
[![python](https://img.shields.io/pypi/pyversions/feeluown.svg)](https://pypi.python.org/pypi/feeluown)

FeelUOwn 是一个稳定、用户友好以及高度可定制的音乐播放器。

[![macOS 效果预览](https://user-images.githubusercontent.com/4962134/73344241-fa5e7280-42bc-11ea-95bf-28eac8180d0e.png)](https://www.bilibili.com/video/av46787694/)

### 特性

- 安装简单，新手友好，默认提供国内各音乐平台插件（网易云、虾米、QQ）
- 基于文本的歌单，方便与朋友分享、设备之间同步
- 提供基于 TCP 的交互控制协议
- 类似 `.vimrc` 和 `.emacs` 的配置文件 `.fuorc`
- 有友善的开发上手文档，核心模块有较好的文档和测试覆盖

### 快速试用

使用系统包管理器一键安装 FeelUOwn 及其扩展吧！

对于 Arch Linux 和 macOS，你可以分别使用如下方式安装：
```sh
# Arch Linux
yay -S feeluown          # 安装稳定版，最新版的包名为 feeluown-git
yay -S feeluown-netease  # 按需安装其它扩展
yay -S feeluown-kuwo
yay -S feeluown-qqmusic
yay -S feeluown-local

# macOS
brew tap feeluown/feeluown
brew install feeluown --with-battery # 安装 FeelUOwn 以及扩展
feeluown genicon                     # 在桌面生成 FeelUOwn 图标
```

Gentoo, NixOS, Debian 等 Linux 发行版也支持使用其系统包管理器安装！
Windows 可以直接下载预打包好的二进制。详情可以参考文档：https://feeluown.readthedocs.io/ ，
也欢迎你加入开发者/用户[交流群](https://t.me/joinchat/H7k12hG5HYsGy7RVvK_Dwg)。

### 免责声明

FeelUown（以下简称“本软件”）是一个个人媒体资源播放工具。本软件提供的所有功能和资料
不得用于任何商业用途。用户可以自由选择是否使用本产品提供的软件。如果用户下载、安装、
使用本软件，即表明用户信任该软件作者，软件作者对任何原因在使用本软件时可能对用户自己
或他人造成的任何形式的损失和伤害不承担责任。

任何单位或个人认为通过本软件提供的功能可能涉嫌侵犯其合法权益，应该及时向 feeluown
组织书面反馈，并提供身份证明、权属证明及详细侵权情况证明，在收到上述法律文件后，
feeluown 组织将会尽快移除被控侵权内容。（联系方式： yinshaowen241 [at] gmail [dot] com ）
