## FeelUOwn - feel your own

[![Documentation Status](https://readthedocs.org/projects/feeluown/badge/?version=latest)](http://feeluown.readthedocs.org)
[![Build Status](https://github.com/feeluown/feeluown/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/feeluown/FeelUOwn)
[![Coverage Status](https://coveralls.io/repos/github/feeluown/FeelUOwn/badge.svg)](https://coveralls.io/github/feeluown/FeelUOwn)
[![PyPI](https://img.shields.io/pypi/v/feeluown.svg)](https://pypi.python.org/pypi/feeluown)
[![python](https://img.shields.io/pypi/pyversions/feeluown.svg)](https://pypi.python.org/pypi/feeluown)

FeelUOwn 是一个稳定、用户友好以及高度可定制的音乐播放器。

[![macOS 效果预览](https://github.com/user-attachments/assets/6d96c655-e35b-46d8-aaec-4d4dc202347f)](https://www.bilibili.com/video/av46787694/)

### 特性

- 稳定、易用：
  - 一键安装，各流行平台均有打包（如 Arch Linux, Windows, macOS 等）
  - 有各媒体资源平台的插件，充分且合理的利用全网免费资源（如 Youtube Music 等）
  - 基础功能完善，桌面歌词、资源智能替换、多音质选择、nowplaying 协议等
  - 核心模块有较好的测试覆盖、核心接口保持较好的向后兼容
  - 大模型加持：AI 电台、自然语言转歌单等
- 可玩性强：
  - 提供基于 TCP 的交互控制协议
  - 基于文本的歌单，方便与朋友分享、设备之间同步
  - 支持基于 Python 的配置文件 `.fuorc`，类似 `.vimrc` 和 `.emacs`

### 快速试用

使用系统包管理器一键安装 FeelUOwn 及其扩展吧！

对于 Arch Linux 和 macOS，你可以分别使用如下方式安装：
```sh
# Arch Linux
yay -S feeluown          # 安装稳定版，最新版的包名为 feeluown-git
yay -S feeluown-netease  # 按需安装其它扩展
yay -S feeluown-ytmusic
yay -S feeluown-bilibili

# macOS（推荐优先尝试在 Release 页面下载打包好的安装包！）
brew tap feeluown/feeluown
brew install feeluown --with-battery # 安装 FeelUOwn 以及扩展
feeluown genicon                     # 在桌面生成 FeelUOwn 图标
```

Windows 和 macOS 用户可以在 Release 页面下载预打包好的二进制。
Gentoo, NixOS, Debian, openSUSE 等 Linux 发行版也支持使用其系统包管理器安装！
详情可以参考文档：https://feeluown.readthedocs.io/ ，
也欢迎你加入开发者/用户[交流群](https://t.me/joinchat/H7k12hG5HYsGy7RVvK_Dwg)。

### 免责声明

FeelUown（以下简称“本软件”）是一个个人媒体资源播放工具。本软件提供的所有功能和资料
不得用于任何商业用途。用户可以自由选择是否使用本产品提供的软件。如果用户下载、安装、
使用本软件，即表明用户信任该软件作者，软件作者对任何原因在使用本软件时可能对用户自己
或他人造成的任何形式的损失和伤害不承担责任。

任何单位或个人认为通过本软件提供的功能可能涉嫌侵犯其合法权益，应该及时向 feeluown
组织书面反馈，并提供身份证明、权属证明及详细侵权情况证明，在收到上述法律文件后，
feeluown 组织将会尽快移除被控侵权内容。（联系方式： yinshaowen241 [at] gmail [dot] com ）
